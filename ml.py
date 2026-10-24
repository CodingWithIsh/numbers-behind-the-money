"""Can route and service features predict what a UK transfer costs?

Target: total cost of sending £120 (% of amount). Unit: one service quote in one survey round.
Time-ordered evaluation: train Q2 2016-Q4 2023, tune on 2024, final test on 2025 (Q1 and Q3).
Metric: mean absolute error (MAE) in percentage points.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

import rpw

CAT = ["destination", "firm_type", "payment instrument", "access point", "pickup method",
       "speed actual", "receiving network coverage"]
NUM = ["t"]
LABELS = {"destination": "Destination country", "firm_type": "Provider type",
          "payment instrument": "How the sender pays", "access point": "Where you send from (online, agent...)",
          "pickup method": "How the money is received", "speed actual": "Speed",
          "receiving network coverage": "Receiving network coverage", "t": "Date (trend)", "firm": "Provider (named)"}


def prepare(df):
    u = rpw.uk(df)
    u = u[u["t"] >= 2016.25].copy()                    # these service fields start in Q2 2016
    u = u[u["total"].notna()]
    for c in CAT + ["firm"]:
        u[c] = (u[c].astype(str).str.strip()
                    .str.replace("Post office", "Post Office", regex=False)
                    .str.replace("Credit Card", "Credit card", regex=False))
    return u


def split(u):
    train = u[u["t"] < 2024]
    valid = u[(u["t"] >= 2024) & (u["t"] < 2025)]
    test = u[u["t"] >= 2025]
    return train, valid, test


def ridge(alpha, cat=CAT):
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=5), cat),
                             ("num", StandardScaler(), NUM)])
    return make_pipeline(pre, Ridge(alpha=alpha))


def gbm(cat=CAT, **kw):
    pre = ColumnTransformer([("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1,
                                                    encoded_missing_value=-1), cat),
                             ("num", "passthrough", NUM)], verbose_feature_names_out=False)
    params = dict(loss="absolute_error", learning_rate=0.05, max_iter=600, max_leaf_nodes=31,
                  min_samples_leaf=20, l2_regularization=1.0, random_state=0)
    params.update(kw)
    model = HistGradientBoostingRegressor(categorical_features=list(range(len(cat))), **params)
    return make_pipeline(pre, model)


class RouteMedian:
    """A sensible non-ML benchmark: predict each destination's median cost in the training data."""
    def fit(self, X, y):
        self.m = pd.Series(y.values, index=X["destination"].values).groupby(level=0).median()
        self.g = float(np.median(y))
        return self
    def predict(self, X):
        return X["destination"].map(self.m).fillna(self.g).values


def run(df, verbose=True):
    u = prepare(df)
    train, valid, test = split(u)
    feats = CAT + NUM
    y = "total"
    log = []

    # tune on 2024
    best_alpha = min([1, 10, 30, 100, 300, 1000],
                     key=lambda a: mean_absolute_error(valid[y], ridge(a).fit(train[feats], train[y]).predict(valid[feats])))
    grid = [dict(learning_rate=lr, max_leaf_nodes=ml) for lr in (0.03, 0.06) for ml in (31, 63, 127)]
    best_gbm = min(grid, key=lambda p: mean_absolute_error(valid[y], gbm(**p).fit(train[feats], train[y]).predict(valid[feats])))
    best_gbm_f = min(grid, key=lambda p: mean_absolute_error(
        valid[y], gbm(cat=CAT + ["firm"], **p).fit(train[feats + ["firm"]], train[y]).predict(valid[feats + ["firm"]])))

    # final: refit on train + 2024, test on 2025
    full = pd.concat([train, valid])
    models = {
        "Baseline: overall median": (DummyRegressor(strategy="median"), feats),
        "Rule of thumb: route median": (RouteMedian(), feats),
        "Linear model (ridge)": (ridge(best_alpha), feats),
        "Gradient boosting": (gbm(**best_gbm), feats),
        "Gradient boosting + provider name": (gbm(cat=CAT + ["firm"], **best_gbm_f), feats + ["firm"]),
    }
    import copy
    results, fitted = [], {}
    for name, (m, f) in models.items():
        v = copy.deepcopy(m).fit(train[f], train[y])              # tuned settings, trained to 2023, scored on 2024
        valid_mae = mean_absolute_error(valid[y], v.predict(valid[f]))
        m.fit(full[f], full[y])                                   # refit to 2024, scored once on 2025
        pred = m.predict(test[f])
        results.append({"model": name, "valid_mae_2024": valid_mae, "test_mae_2025": mean_absolute_error(test[y], pred)})
        fitted[name] = (m, f, pred)
    res = pd.DataFrame(results).set_index("model")

    # permutation importance for the main model (no provider name), on the 2025 test set
    m, f, pred = fitted["Gradient boosting"]
    pi = permutation_importance(m, test[f], test[y], scoring="neg_mean_absolute_error", n_repeats=10, random_state=0)
    imp = pd.Series(pi.importances_mean, index=f).sort_values(ascending=False)

    # where the model does well / badly
    t2 = test.assign(pred=pred, err=(test[y] - pred).abs())
    by_pickup = t2.groupby("pickup method").agg(n=("err", "size"), mae=("err", "mean")).sort_values("n", ascending=False).head(4)
    by_route = t2.groupby("destination").agg(n=("err", "size"), mae=("err", "mean")).sort_values("mae")

    info = dict(n_train=len(train), n_valid=len(valid), n_test=len(test), best_alpha=best_alpha,
                best_gbm=best_gbm, best_gbm_f=best_gbm_f, test_median=float(test[y].median()))
    if verbose:
        print(info); print(res.round(3)); print(imp.round(3)); print(by_pickup.round(2)); print(by_route.round(2).iloc[[0, 1, 2, -3, -2, -1]])
    return res, imp, info, by_pickup, by_route
