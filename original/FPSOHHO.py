import math
import time
import numpy as np


class FPSOHHO:
    def __init__(self, fitness_func, lb=-5, ub=5, dimension=30, pop_size=50,
                 max_iter=1000, c1=2.0, c2=2.0, w_start=0.9, w_end=0.4,
                 alpha_start=1.0, alpha_end=0.2, v_max=5.0, switch_iter_ratio=0.1):
        self.fitness_func = fitness_func
        self.dimension = dimension
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.lb = lb
        self.ub = ub
        self.c1 = c1
        self.c2 = c2
        self.w_start = w_start
        self.w_end = w_end
        self.alpha_start = alpha_start
        self.alpha_end = alpha_end
        self.v_max = v_max
        self.switch_iter = int(max_iter * switch_iter_ratio)

        self.X = np.random.uniform(lb, ub, (pop_size, dimension))
        self.X = np.clip(self.X, lb, ub)
        self.V = np.random.uniform(-v_max, v_max, (pop_size, dimension))
        self.V = np.clip(self.V, -v_max, v_max)

        self.p_best = np.copy(self.X)
        self.gen_best = self.find_global_best(self.X)
        self.g_best = self.gen_best.copy()

        self.Rabbit_Location = self.g_best.copy()
        self.Rabbit_Energy = np.inf
        self.sync_rabbit()
        self.gBest_curve = np.zeros(max_iter)
        self.no_improve_count = 0
        self.last_best_energy = self.Rabbit_Energy

    def get_dynamic_params(self, t):
        w = self.w_start - (self.w_start - self.w_end) * (t / self.max_iter)
        alpha = self.alpha_start - (self.alpha_start - self.alpha_end) * (t / self.max_iter)
        return w, alpha

    def update_velocity(self, t):
        w, alpha = self.get_dynamic_params(t)
        r1 = np.random.rand(self.pop_size, self.dimension)
        r2 = np.random.rand(self.pop_size, self.dimension)

        # MSPSO核心部分：三种引导合成
        cognitive_term = (1 - alpha) * (self.p_best - self.X) + alpha * (self.gen_best - self.X)
        social_term = self.g_best - self.X

        self.V = w * self.V + self.c1 * r1 * cognitive_term + self.c2 * r2 * social_term
        self.V = np.clip(self.V, -self.v_max, self.v_max)

    def update_position(self):
        self.X = self.X + self.V
        self.X = np.clip(self.X, self.lb, self.ub)

    def hho_search(self, t):
        E1 = 2 * (1 - (t / self.max_iter))
        for i in range(self.pop_size):
            E0 = 2 * np.random.rand() - 1
            Escaping_Energy = E1 * E0

            if abs(Escaping_Energy) >= 1:
                q = np.random.rand()
                if q < 0.5:
                    rand_Hawk_idx = np.random.randint(0, self.pop_size)
                    X_rand = self.X[rand_Hawk_idx]
                    self.X[i] = X_rand - np.random.rand() * abs(X_rand - 2 * np.random.rand() * self.X[i])
                else:
                    self.X[i] = (self.Rabbit_Location - self.X.mean(axis=0)) - np.random.rand() * (self.ub - self.lb)
            else:
                r = np.random.rand()
                Jump_strength = 2 * (1 - np.random.rand())
                if r >= 0.5 and abs(Escaping_Energy) < 0.5:
                    self.X[i] = self.Rabbit_Location - Escaping_Energy * abs(self.Rabbit_Location - self.X[i])
                elif r >= 0.5:
                    self.X[i] = (self.Rabbit_Location - self.X[i]) - Escaping_Energy * abs(
                        Jump_strength * self.Rabbit_Location - self.X[i])
                elif abs(Escaping_Energy) >= 0.5:
                    X1 = self.Rabbit_Location - Escaping_Energy * abs(Jump_strength * self.Rabbit_Location - self.X[i])
                    if self.fitness_func(X1) < self.fitness_func(self.X[i]):
                        self.X[i] = X1
                    else:
                        X2 = X1 + np.random.randn(self.dimension) * self.Levy(self.dimension)
                        if self.fitness_func(X2) < self.fitness_func(self.X[i]):
                            self.X[i] = X2
                else:
                    X1 = self.Rabbit_Location - Escaping_Energy * abs(
                        Jump_strength * self.Rabbit_Location - self.X.mean(axis=0))
                    if self.fitness_func(X1) < self.fitness_func(self.X[i]):
                        self.X[i] = X1
                    else:
                        X2 = X1 + np.random.randn(self.dimension) * self.Levy(self.dimension)
                        if self.fitness_func(X2) < self.fitness_func(self.X[i]):
                            self.X[i] = X2
            self.X[i] = np.clip(self.X[i], self.lb, self.ub)

    @staticmethod
    def Levy(dim):
        beta = 1.5
        sigma = (math.gamma(1 + beta) * math.sin(math.pi * beta / 2) /
                 (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))) ** (1 / beta)
        u = 0.01 * np.random.randn(dim) * sigma
        v = np.random.randn(dim)
        zz = np.power(np.absolute(v), (1 / beta))
        return np.divide(u, zz)

    def optimize(self):
        self.timerStart = time.time()

        self.sync_rabbit()
        self.gBest_curve[0] = self.Rabbit_Energy
        print(f"Iter 0: FPSOHHO当前最优适应度={self.Rabbit_Energy}")

        for t in range(1, self.max_iter):
            if t < self.switch_iter:
                self.hho_search(t)
            else:
                self.update_velocity(t)
                self.update_position()

            self.update_p_best()
            self.update_gen_g_best()
            self.sync_rabbit()

            self.gBest_curve[t] = self.Rabbit_Energy
            print(f"Iter {t}: FPSOHHO当前最优适应度={self.Rabbit_Energy}")

            if abs(self.Rabbit_Energy - self.last_best_energy) < 1e-5:
                self.no_improve_count += 1
            else:
                self.no_improve_count = 0
                self.last_best_energy = self.Rabbit_Energy

            if self.no_improve_count >= 10:
                self.perturb_particles()
                self.no_improve_count = 0

        self.executionTime = time.time() - self.timerStart
        return self.gBest_curve, self.Rabbit_Energy, self.Rabbit_Location, time.strftime(
            "%Y-%m-%d-%H-%M-%S"), self.executionTime

    def perturb_particles(self):
        num_perturb = int(self.pop_size * 0.2)
        for i in np.random.choice(self.pop_size, num_perturb, replace=False):
            self.X[i] = np.random.uniform(self.lb, self.ub, self.dimension)

    def sync_rabbit(self):
        current_best = self.find_global_best(self.X)
        current_energy = self.fitness_func(current_best)
        if current_energy < self.Rabbit_Energy:
            self.Rabbit_Energy = current_energy
            self.Rabbit_Location = current_best.copy()
            self.g_best = current_best.copy()

    def find_global_best(self, positions):
        fitness = np.array([self.fitness_func(pos) for pos in positions])
        valid_mask = fitness < 1e5
        if not np.any(valid_mask):
            return positions[0]
        return positions[np.argmin(fitness)]

    def update_p_best(self):
        for i in range(self.pop_size):
            if self.fitness_func(self.X[i]) < self.fitness_func(self.p_best[i]):
                self.p_best[i] = self.X[i].copy()

    def update_gen_g_best(self):
        current_gen_best = self.find_global_best(self.X)
        if self.fitness_func(current_gen_best) < self.fitness_func(self.gen_best):
            self.gen_best = current_gen_best.copy()
        if self.fitness_func(current_gen_best) < self.fitness_func(self.g_best):
            self.g_best = current_gen_best.copy()

    def return_gBest_curve(self):
        return self.gBest_curve
