import numpy as np

def uniform_intervals(a, b, n):
    return np.linspace(a, b, n)
    pass

def cyclic123_array(n):
    return np.tile([1, 2, 3], n)
    pass

def first_n_odd_number(n):
    return np.arange(1, 2 * n, 2)
    pass

def zeros_array_with_border(n):
    arr = np.zeros((n, n), dtype=int)
    arr[0, :] = 1      # Верхняя граница
    arr[-1, :] = 1     # Нижняя граница
    arr[:, 0] = 1      # Левая граница
    arr[:, -1] = 1     # Правая граница
    return arr
    pass

def chess_board(n):
    return (np.indices((n, n)).sum(axis=0)+1) % 2
    pass

def matrix_with_sum_index(n):
    rows = np.arange(n).reshape(-1, 1)
    cols = np.arange(n)
    return rows + cols
    pass

def cos_sin_as_two_rows(a, b, dx):
    x = np.arange(a, b, dx)
    cos_vals = np.cos(x) 
    sin_vals = np.sin(x)
    return np.vstack((cos_vals, sin_vals))
    pass

def compute_mean_rowssum_columnssum(A):
    return np.mean(A), np.sum(A, axis=0), np.sum(A, axis=1)
    pass

def sort_array_by_column(A, j):
    return A[A[:, j].argsort()]
    pass

def compute_integral(a, b, f, dx, method):
    x = np.arange(a, b + dx, dx)  # Точки интегрирования (включая правую границу)
    y = f(x)
    
    if method == 'rectangular':
        # Метод прямоугольников
        return np.sum(y[:-1] * dx)
    elif method == 'trapezoidal':
        # Метод трапеций
        return np.sum((y[:-1] + y[1:]) * dx / 2)
    elif method == 'simpson':
        # Метод Симпсона
        if (len(x) - 1) % 2 != 0:
            # Если число интервалов нечетное, уменьшаем шаг на последнем интервале
            last_dx = b - x[-2]
            simpson_part = (y[-3] + 4*y[-2] + y[-1]) * last_dx / 6
            return (np.sum(y[:-3:2] + 4*y[1:-2:2] + y[2:-1:2]) * dx / 3) + simpson_part
        return np.sum(y[:-1:2] + 4*y[1::2] + y[2::2]) * dx / 3
        pass