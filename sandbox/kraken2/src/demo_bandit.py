# %%

from bandit import ContextualBandit
from pprint import pprint
from random import choice

bandit = ContextualBandit(item_id='content_serie:1')
bandit.n_arms = 2
bandit.b_len = 4
bandit.delta = 0.1
bandit.R = 0.1

# %%
b = [1, 0, 1, 0]
arm = bandit.select_arm(b)
pprint(vars(bandit))

# %%
b = [0, 1, 1, 0]
arm = bandit.select_arm(b)
pprint(vars(bandit))

# %%
for _ in range(1000):
    b = choice([[0, 1, 1, 0],
                [1, 0, 1, 0],
                [1, 0, 0, 1],
                [0, 0, 1, 1]])
    arm = bandit.select_arm(b)

# %%
bandit.assign_random_rewards(weights=[0.8, 1])
for a in range(bandit.n_arms):
    bandit.calculate_mu_hat(a)
pprint(bandit.get_history_stats())

# %%
for _ in range(9):
    for _ in range(1000):
        b = choice([[0, 1, 1, 0],
                    [1, 0, 1, 0],
                    [1, 0, 0, 1],
                    [0, 0, 1, 1]])
        arm = bandit.select_arm(b)
    bandit.assign_random_rewards(weights=[0.8, 1])
    for a in range(bandit.n_arms):
        bandit.calculate_mu_hat(a)
pprint(bandit.get_history_stats())
