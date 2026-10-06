DATA 52 1
DATA 53 0
# Multiplicacion: primer entero libre, segundo entero no negativo.
# Entrada de datos
INPUT
STORE 50
INPUT
STORE 51

# Validar si alguno es cero
LOAD 50
JZ 18
LOAD 51
JZ 18

# Bucle de multiplicacion
LOAD 53
ADD 50
STORE 53
LOAD 51
SUB 52
STORE 51
JNZ 8

# Imprimir resultado normal
LOAD 53
OUTPUT
HALT

# Rutina para caso cero
LOAD 53
OUTPUT
HALT