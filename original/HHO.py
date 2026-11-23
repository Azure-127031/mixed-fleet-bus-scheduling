import numpy as np
import math


class HHO:
    def __init__(self, fitness_func, lb=-5, ub=5, dimension=30, pop_size=50, max_iter=1000):
        self.fitness_func = fitness_func
        self.lb = lb
        self.ub = ub
        self.dimension = dimension
        self.pop_size = pop_size
        self.max_iter = max_iter

        # 初始化种群位置
        self.X = np.random.uniform(lb, ub, (pop_size, dimension))
        self.gBest_curve = np.zeros(max_iter)

        # 初始化 Rabbit
        fitness_vals = np.array([self.safe_fitness(x) for x in self.X])
        best_idx = np.argmin(fitness_vals)
        self.Rabbit_Location = self.X[best_idx].copy()
        self.Rabbit_Energy = fitness_vals[best_idx]

    def safe_fitness(self, x):
        """目标函数容错处理"""
        try:
            if len(x) != self.dimension or np.any(np.isnan(x)) or np.any(~np.isfinite(x)):
                return 1e20
            if np.any(x < self.lb) or np.any(x > self.ub):
                return 1e20
            val = self.fitness_func(x)
            if not np.isfinite(val) or abs(val) > 1e19:
                return 1e20
            return val
        except Exception as e:
            print(f"[目标函数异常] {e}")
            return 1e20

    def levy(self, dim):
        beta = 1.5
        sigma = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2) /
                 (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)
        u = np.random.randn(dim) * sigma
        v = np.random.randn(dim)
        return u / (np.abs(v) ** (1 / beta))

    def optimize(self):
        print(f"Iter 0: 初始最优适应度 = {self.Rabbit_Energy:.6f}")

        for t in range(self.max_iter):
            E1 = 2 * (1 - t / self.max_iter)

            for i in range(self.pop_size):
                E0 = 2 * np.random.rand() - 1
                escaping_energy = E1 * E0
                jump_strength = np.clip(2 * (1 - np.random.rand()), 0.1, 2.0)
                fitness_i = self.safe_fitness(self.X[i])

                if abs(escaping_energy) >= 1:
                    q = np.random.rand()
                    rand_idx = np.random.randint(0, self.pop_size)
                    X_rand = self.X[rand_idx]
                    if q < 0.5:
                        self.X[i] = X_rand - np.random.rand() * np.abs(X_rand - 2 * np.random.rand() * self.X[i])
                    else:
                        self.X[i] = (self.Rabbit_Location - np.mean(self.X, axis=0)) - \
                                    np.random.rand() * (self.ub - self.lb) * np.random.rand()
                else:
                    r = np.random.rand()
                    if r >= 0.5 and abs(escaping_energy) < 0.5:
                        self.X[i] = self.Rabbit_Location - escaping_energy * np.abs(
                            self.Rabbit_Location - self.X[i])
                    elif r >= 0.5 and abs(escaping_energy) >= 0.5:
                        self.X[i] = (self.Rabbit_Location - self.X[i]) - escaping_energy * np.abs(
                            jump_strength * self.Rabbit_Location - self.X[i])
                    elif r < 0.5 and abs(escaping_energy) >= 0.5:
                        X1 = self.Rabbit_Location - escaping_energy * np.abs(
                            jump_strength * self.Rabbit_Location - self.X[i])
                        if self.safe_fitness(X1) < fitness_i:
                            self.X[i] = X1
                        else:
                            X2 = X1 + self.levy(self.dimension) * np.random.randn(self.dimension)
                            if self.safe_fitness(X2) < fitness_i:
                                self.X[i] = X2
                    else:
                        X1 = self.Rabbit_Location - escaping_energy * np.abs(
                            jump_strength * self.Rabbit_Location - np.mean(self.X, axis=0))
                        if self.safe_fitness(X1) < fitness_i:
                            self.X[i] = X1
                        else:
                            X2 = X1 + self.levy(self.dimension) * np.random.randn(self.dimension)
                            if self.safe_fitness(X2) < fitness_i:
                                self.X[i] = X2

                # 边界限制
                self.X[i] = np.clip(self.X[i], self.lb, self.ub)

                # 更新最优个体
                new_fit = self.safe_fitness(self.X[i])
                if new_fit < self.Rabbit_Energy:
                    self.Rabbit_Energy = new_fit
                    self.Rabbit_Location = self.X[i].copy()

            self.gBest_curve[t] = self.Rabbit_Energy

            if self.Rabbit_Energy >= 1e19:
                print(f"⚠️ 第{t}轮适应度异常为1e20，请检查目标函数")
            else:
                print(f"Iter {t}: HHO当前最优适应度 = {self.Rabbit_Energy:.6e}")

        return self.gBest_curve, self.Rabbit_Energy, self.Rabbit_Location

    def return_pBest_curve(self):
        return self.gBest_curve
