import pandas as pd
import numpy as np


############################
# ALPHA FUNCTIONS
############################

def ts_mean(s, w):
    return s.rolling(w).mean()

def ts_std(s, w):
    return s.rolling(w).std()

def ts_delta(s, p):
    return s.diff(p)

def ts_rank(s, w):
    return s.rolling(w).rank(pct=True)

def cs_rank(s):
    return s.rank(pct=True)

def ts_delay(s, p):
    return s.shift(p)


############################
# CORE BACKTEST
############################

def compute_alpha(df, formula_code):

    df = df.copy()

    local_dict = {
        "close": df["close"],
        "open": df["open"],
        "high": df["high"],
        "low": df["low"],
        "volume": df["volume"],

        # 🔥 FIX
        #"net_income": df.get("net_income", pd.Series(0, index=df.index)),

        #"foreign_buy_val": df.get("foreign_buy_val", pd.Series(0, index=df.index)),
        #"foreign_sell_val": df.get("foreign_sell_val", pd.Series(0, index=df.index)),

        "ts_mean": ts_mean,
        "ts_std": ts_std,
        "ts_delta": ts_delta,
        "ts_rank": ts_rank,
        "cs_rank": cs_rank,
        "ts_delay": ts_delay,   # 🔥 ADD

        "np": np
    }

    alpha_series = eval(formula_code, {"__builtins__": None}, local_dict)

    df["alpha"] = alpha_series

    alpha = df.pivot(index="time", columns="symbol", values="alpha")

    return alpha


def compute_returns(df):

    price = df.pivot(index="time", columns="symbol", values="close")

    returns = price.pct_change()

    return returns


def rank_stocks(alpha):

    return alpha.rank(axis=1, pct=True)


def build_portfolio(rank, top_pct=0.2):

    return (rank > (1 - top_pct)).astype(int)


def compute_strategy_returns(position, returns):

    return (position.shift(1) * returns).mean(axis=1)


def compute_ic(alpha, returns):

    future_returns = returns.shift(-1)

    ic_series = alpha.corrwith(future_returns, axis=1)

    return ic_series.mean()


def compute_sharpe(strategy_returns):

    return np.sqrt(252) * strategy_returns.mean() / strategy_returns.std()


def compute_equity_curve(strategy_returns):

    return (1 + strategy_returns.fillna(0)).cumprod()


############################
# MAIN ENTRY
############################

def run_backtest(df, formula_code):

    alpha = compute_alpha(df, formula_code)

    returns = compute_returns(df)

    rank = rank_stocks(alpha)

    position = build_portfolio(rank)

    strat_returns = compute_strategy_returns(position, returns)

    ic = compute_ic(alpha, returns)

    sharpe = compute_sharpe(strat_returns)

    equity = compute_equity_curve(strat_returns)

    total_return = equity.iloc[-1] - 1

    entry_ratio = position.mean().mean()

    return {
        "IC": ic,
        "Sharpe": sharpe,
        "Total Return": total_return,
        "Entry Ratio": entry_ratio,
        "Equity Curve": equity
    }


def alpha_backtester(state):

    df = pd.read_csv("D://TestMLPy//alpha//src//market_stocks.csv")
    coded_alphas = state.coded_alphas

    results = []

    for alpha in coded_alphas:

        try:
            metrics = run_backtest(df, alpha["code"])

            results.append({
                **alpha,
                "metrics": metrics
            })

        except Exception as e:

            results.append({
                **alpha,
                "error": str(e)
            })

    return {
        "backtest_results": results
    }