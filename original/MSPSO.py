import numpy as np


class MSPSO:
    def __init__(self, fitness_func, c1=2.0, c2=2.0, lb=-5, ub=5, dimension=30,
                 pop_size=50, max_iter=1000, w_start=0.9, w_end=0.4,
                 alpha_start=1.0, alpha_end=0.2, v_max=5.0):
        self.fitness_func = fitness_func
        self.lb = lb
        self.ub = ub
        self.dimension = dimension
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.c1 = c1  # 个体认知系数
        self.c2 = c2  # 社会系数
        self.w_start = w_start  # 惯性权重初始值
        self.w_end = w_end      # 惯性权重终值
        self.alpha_start = alpha_start  # 初始种群最优权重
        self.alpha_end = alpha_end      # 最终个体最优权重
        self.v_max = v_max    # 最大速度限制

        # 初始化位置、速度和个体最优
        self.X = np.random.uniform(self.lb, self.ub, (self.pop_size, self.dimension))
        self.V = np.random.uniform(-self.v_max, self.v_max, (self.pop_size, self.dimension))
        self.p_best = np.copy(self.X)

        # 初始化全局最优与代最优
        self.g_best, self.g_best_fitness = self.find_global_best(self.X)
        self.gen_best = self.g_best.copy()

        self.evolution = []

    def get_dynamic_params(self, t):
        w = self.w_start - (self.w_start - self.w_end) * (t / self.max_iter)
        alpha = self.alpha_start - (self.alpha_start - self.alpha_end) * (t / self.max_iter)
        return w, alpha

    def update_velocity(self, t):
        w, alpha = self.get_dynamic_params(t)
        r1 = np.random.rand(self.pop_size, self.dimension)
        r2 = np.random.rand(self.pop_size, self.dimension)
        cognitive_term = (1 - alpha) * (self.p_best - self.X) + alpha * (self.gen_best - self.X)
        social_term = self.g_best - self.X
        self.V = w * self.V + self.c1 * r1 * cognitive_term + self.c2 * r2 * social_term
        self.V = np.clip(self.V, -self.v_max, self.v_max)

    def update_positions(self):
        self.X = self.X + self.V
        self.X = np.clip(self.X, self.lb, self.ub)

    def find_global_best(self, positions):
        fitness = np.array([self.fitness_func(x) for x in positions])
        best_idx = np.argmin(fitness)
        return positions[best_idx].copy(), fitness[best_idx]

    def update_p_best(self):
        for i in range(self.pop_size):
            current_fit = self.fitness_func(self.X[i])
            if current_fit < self.fitness_func(self.p_best[i]):
                self.p_best[i] = self.X[i].copy()

    def update_bests(self):
        current_gen_best, current_gen_fitness = self.find_global_best(self.X)
        if current_gen_fitness < self.fitness_func(self.gen_best):
            self.gen_best = current_gen_best.copy()
        if current_gen_fitness < self.g_best_fitness:
            self.g_best = current_gen_best.copy()
            self.g_best_fitness = current_gen_fitness

    def optimize(self):
        # 初始记录（确保收敛曲线首项有值）
        self.update_bests()
        self.evolution.append(self.g_best_fitness)
        print(f"Iteration 0: MSPSO初始最优适应度 = {self.g_best_fitness:.6f}")

        for t in range(1, self.max_iter):
            self.update_p_best()
            self.update_bests()
            self.update_velocity(t)
            self.update_positions()

            self.evolution.append(self.g_best_fitness)
            print(f"Iteration {t}: MSPSO当前最优适应度 = {self.g_best_fitness:.6e}")

        return self.evolution

    def return_result(self):
        return self.evolution