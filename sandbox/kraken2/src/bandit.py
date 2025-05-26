import statistics
import numpy as np
from math import sqrt, log


class ContextualBandit:
    """
    REF: Thompson Sampling for Contextual Bandits with Linear Payoffs (2014)
    REF: https://arxiv.org/pdf/1209.3352
    """

    def __init__(self, item_id):
        # TODO: seed ???
        self.item_id = item_id
        self.n_arms = self.init_n_arms()
        self.b_len = self.init_b_len()
        self.delta = self.init_delta()
        self.R = self.init_R()
        self.state = {}

    def select_arm(self, b):
        # cast b to np.array
        b = np.array(b)
        n_arms = self.n_arms
        v = self.get_v()
        B_inv = self.get_B_inv()
        cov = B_inv * v**2

        predicted_rewards = np.zeros(n_arms)
        for arm in range(n_arms):
            mu_hat = self.get_mu_hat(arm)
            mu_tilde = np.random.multivariate_normal(mu_hat, cov=cov)
            predicted_rewards[arm] = b.T @ mu_tilde
        arm = np.argmax(predicted_rewards).astype(int)
        self.save_history(arm, b, reward=None)
        self.update_B(b)
        # self.update_mu()  # not called as we don't have reward yet
        self.update_t()
        return arm

    # B ralated

    def init_B(self):
        B = np.eye(self.b_len)
        self.state["B"] = B

    def get_B(self):
        if "B" not in self.state:
            self.init_B()
        return self.state["B"]

    def update_B(self, b):
        b = b.reshape(1, -1)
        delta = b * b.T
        self.state["B"] = self.get_B() + delta

    def get_B_inv(self):
        B = self.get_B()
        return np.linalg.inv(B)

    # mu related

    def init_mu_hat(self):
        self.state["mu_hat"] = {i: np.zeros(self.b_len) for i in range(self.n_arms)}

    def get_mu_hat(self, arm):
        if "mu_hat" not in self.state:
            self.init_mu_hat()
        return self.state["mu_hat"][arm]

    def calculate_mu_hat(self, arm):
        B_inv = self.get_B_inv()
        b_reward_agg = self.get_b_reward_agg(arm)
        mu_hat = B_inv @ b_reward_agg
        self.state["mu_hat"][arm] = mu_hat

    # history related

    def save_history(self, arm, b, reward):
        if "history_cnt" not in self.state:
            self.init_history_cnt()
        if "history" not in self.state:
            self.init_history()
        t = self.get_t()
        self.state["history"][arm].append([t, reward, b])
        self.state["history_cnt"][arm] += 1

    def init_history(self):
        self.state["history"] = {i: [] for i in range(self.n_arms)}

    def init_history_cnt(self):
        self.state["history_cnt"] = {i: 0 for i in range(self.n_arms)}

    def get_history(self, arm):
        if "history" not in self.state:
            self.init_history()
        return self.state["history"][arm]

    def get_b_reward_agg(self, arm):
        history = self.get_history(arm)
        b_reward_agg = np.zeros(self.b_len)
        for t, reward, b in history:
            if reward:
                b_reward_agg += b * reward
        return b_reward_agg

    # other

    def get_v(self):
        delta = self.delta
        R = self.R
        d = self.b_len
        t = self.get_t()
        return R * sqrt(9 * d * log(t/delta))

    def update_t(self):
        self.state["t"] = self.get_t() + 1

    def get_t(self):
        if "t" not in self.state:
            self.init_t()
        return self.state["t"]

    def init_t(self):
        self.state["t"] = 1

    def init_R(self):
        return 1

    def init_delta(self):
        return 0.05

    def init_n_arms(self):
        return ...  # TODO: get from config

    def init_b_len(self):
        return ...  # TODO: get from config

    def assign_random_rewards(self, weights=None):
        "for demo/testing purposes only"
        if weights is None:
            weights = [1] * self.n_arms
        for arm in self.state["history"]:
            for i in range(len(self.state["history"][arm])):
                reward = self.state["history"][arm][i][1]
                if reward is None:
                    # Generate random reward in range [0, 1] weighted by arm's weight
                    base_reward = np.random.random()
                    random_reward = base_reward * weights[arm]
                    self.state["history"][arm][i][1] = round(random_reward, 2)

    def get_history_stats(self):
        "for demo/testing purposes only"
        from statistics import mean, stdev
        stats = {}
        for arm in self.state["history"]:
            history = self.get_history(arm)
            rewards = [h[1] for h in history]
            stats[arm] = {
                "mean": round(mean(rewards), 3),
                "stddev": round(stdev(rewards), 3),
                "cnt": len(rewards),
            }
        return stats
