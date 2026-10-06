DATA 50 3
DATA 51 1
DATA 52 0

# Prueba 5 - Bucle con JNZ
# Datos iniciales: Mem[50] = 3, Mem[51] = 1, Mem[52] = 0
# Calcula 3 + 2 + 1
# Esperado: ACC = 6 y Mem[53] = 6
LOAD 50
STORE 54
LOAD 52
STORE 53
LOAD 53
ADD 54
STORE 53
LOAD 54
SUB 51
STORE 54
JNZ 4
LOAD 53
OUTPUT
HALT
