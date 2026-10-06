DATA 10 50
DATA 11 30

# Prueba 2 - Resta
# Datos iniciales: Mem[10] = 50, Mem[11] = 30
# Esperado: ACC = 20 y Mem[20] = 20
LOAD 10
SUB 11
STORE 20
OUTPUT
HALT
