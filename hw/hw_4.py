import numpy as np

def solve():
    import sys
    input = sys.stdin.read().split('\n')
    ptr = 0
    
    # Чтение размеров m, n
    while ptr < len(input) and input[ptr].strip() == '':
        ptr += 1
    m, n = map(int, input[ptr].strip().split())
    ptr += 1
    
    # Чтение матрицы A
    A = []
    for _ in range(m):
        while ptr < len(input) and input[ptr].strip() == '':
            ptr += 1
        row = list(map(int, input[ptr].strip().split(',')))
        A.append(row)
        ptr += 1
    A = np.array(A, dtype=np.int32)
    
    # Чтение размеров h, w
    while ptr < len(input) and input[ptr].strip() == '':
        ptr += 1
    h, w = map(int, input[ptr].strip().split())
    ptr += 1
    
    # Чтение матрицы C
    C = []
    for _ in range(m):
        while ptr < len(input) and input[ptr].strip() == '':
            ptr += 1
        row = list(map(int, input[ptr].strip().split(',')))
        C.append(row)
        ptr += 1
    C = np.array(C, dtype=np.int32)
    
    # Определение паддинга
    pad_h = (h - 1) // 2
    pad_w = (w - 1) // 2
    
    # Создание системы уравнений для нахождения B
    equations = []
    rhs = []
    
    for i in range(m):
        for j in range(n):
            # Для каждого пикселя C[i,j] формируем уравнение
            equation = np.zeros((h, w), dtype=np.int32)
            for k in range(h):
                for r in range(w):
                    a_i = i - k + pad_h
                    a_j = j - r + pad_w
                    if 0 <= a_i < m and 0 <= a_j < n:
                        equation[k, r] = A[a_i, a_j]
            equations.append(equation.flatten())
            rhs.append(C[i, j])
    
    # Преобразуем уравнения в матрицу коэффициентов
    A_matrix = np.array(equations, dtype=np.int32)
    b_vector = np.array(rhs, dtype=np.int32)
    
    # Решаем систему линейных уравнений
    B_flat, residuals, rank, singular_values = np.linalg.lstsq(A_matrix, b_vector, rcond=None)
    
    # Преобразуем решение обратно в матрицу h x w
    B = np.round(B_flat).reshape((h, w)).astype(np.int32)
    
    # Выводим результат
    for i in range(h):
        row = ','.join(map(str, B[i].tolist()))
        print(row)

if __name__ == '__main__':
    solve()