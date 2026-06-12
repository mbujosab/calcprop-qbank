BloqueDeEnunciado = [
    r"En el ajuste MCO:\; $\ajusteMLG$,\; ",
    [
        Supuesto(r"donde $\Matdim{X}{N}{k}$, si $rg(\Mat{X})<k$, con $k \leq N$,",         v("Mcoli")),    
        Supuesto(r"si $(\MTM{X})$ es singular,",                                         v("Mcoli")),    
        Supuesto(r"donde $\Matdim{X}{N}{k}$, si $rg(\Mat{X})=k$, con $k \leq N$,",        -v("Mcoli")),
        Supuesto(r"si $(\MTM{X})$ es invertible,",                                        -v("Mcoli")),    
    ],
    " entonces: ",]

BloqueDeCuestiones = [
    [
        Cuestion("ningún regresor es combinación lineal del resto",                        -v("Mcoli"),
                 exp=r"cuando $(\MTM{X})$ es invertible, es decir, cuando $rg(\Mat{X}) = k$"),
        Cuestion(r"las \emph{columnas} de $\Mat{X}$ son linealmente indep.",               -v("Mcoli"),
                 exp=r"cuando $(\MTM{X})$ es invertible, es decir, cuando $rg(\Mat{X}) = k$"),    
        Cuestion(r"las \emph{filas} de $\Mat{X}$ son linealmente indep.",                        False,
                 exp=r"solo si $N=rg(\Mat{X})$"),    
        Cuestion("algún regresor es combinación lineal del resto",                          v("Mcoli"),
                 exp=r"cuando $(\MTM{X})$ es singular, es decir, cuando $rg(\Mat{X}) < k$"),
    ],
    [
        Cuestion(r"$\Vect{y}$ es combinación lineal de los regresores",                        False , -v("Mcoli"),
                 exp=r"cuando $\Vect{y}$ es de la forma $\MV{X}{\beta}$, es decir cuando $\res=\Vect{0}$"),    
        Cuestion(r"$\MTM{X}\Vect{\beta}=\MTV{X}{y}$ tiene solución \emph{única}",          -v("Mcoli"),
                 exp=r"cuando $(\MTM{X})$ es invertible, es decir, cuando $rg(\Mat{X}) = k$"),
        Cuestion(r"$\MTM{X}\Vect{\beta}=\MTV{X}{y}$ es compatible (tiene sol.)",                 True,
                 exp=r"las ecuaciones normales siempre tienen solución"),
    ],
    [
        Cuestion(r"el vector $\Estmc{\Vect{\beta}}$ está definido",                        -v("Mcoli"),
                 exp=r"cuando $\MTM{X}\Vect{\beta}=\MTV{X}{y}$ tiene solución \emph{única}"),    
        Cuestion(r"el vector $\Estmc{\Vect{\beta}}$ es indeterminado",                      v("Mcoli"),
                 exp=r"cuando $\MTM{X}\Vect{\beta}=\MTV{X}{y}$ tiene infinitas soluciones"),    
        Cuestion("la correlación entre algunos regresores es 1 en valor absoluto",               False,
                 exp=r"cuando algún regresor es un múltiplo de otro"),    
        Cuestion("la correlación entre regresores es \emph{menor} que 1 en valor absoluto",-v("Mcoli"),
                 exp=r"cuando los regresores son linealmente independientes"),
    ],]

p = [ BloqueDeEnunciado + BloqueDeCuestiones ]

directorio = "../ejemplos/"           # directorio donde vamos a guardar el fichero resultante
nombre="L-01-EcNormales-RangoX"       # Etiqueta del conjunto de preguntas
mc=2;                                 # cuestiones a doble columna
preguntas = {}; 
preguntas[nombre] = ProblemaTipo( p )
with open(directorio + nombre + ".tex","w") as f:
    for i,nom in enumerate(preguntas):
        for var in preguntas[nom]:
            f.write( AMClastChmc(nombre, str(i)+"-"+var[0], var[1], var[2], mc, ["","Ninguna de las anteriores"]) )
