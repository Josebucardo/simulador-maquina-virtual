DATA 10 20
DATA 11 20
DATA 12 111
DATA 13 999

# Prueba 4 - Condicional con JZ
# Datos iniciales: Mem[10] = 20, Mem[11] = 20, Mem[12] = 111, Mem[13] = 999
# Esperado: ACC = 111 porque 20 - 20 activa la bandera Z
LOAD 10
SUB 11
JZ 6
LOAD 13
OUTPUT
HALT
LOAD 12
OUTPUT
HALT
