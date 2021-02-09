# Tracer
Traceur de courbes basé sur matplotlib.

Test rapide, dans un terminal :

`$ { while true ; do echo $((RANDOM%21-10)) $((RANDOM%21-10)) ; sleep 0.01 ; done } | ./tracer.py -C1/2 -b200`


**Les fichiers :**

tracer-qt4.py et tracer-tk.py propose respectivement une interface graphique à partir des bibliothèque Qt4 et Tkinter. Ils utilisent tous deux la classe `Tracer` définie dans tracer.py. Ce dernier fichier peut être exécuté directement, dans quel cas l'interface standard de matplotlib sera utilisée et la barre d'outils ne se verra pas agrémenté des boutons "change band/rate", "pause" et "save data". tracer-qt4.py et tracer-tk.py servent d'exemples pour la manière d'intégrer le traceur et sa barre d'outils dans n'importe quelle application.


**Le traceur en lui-même :**

Le traceur peut lire depuis un fichier texte, un tube ou un socket. Dans ces deux derniers cas, les courbes seront actualisées à une période qui peut être définie par l'option `-r, --rate` (50 ms par défaut) lorsque de nouvelles valeurs arrivent. Si le traceur est surchargé par l'arrivée des nouvelles données, il diffèrera l'actualisation des courbes afin de rester à jour. Lorsque cela arrive, la mention "OVERRUN" s'affiche en haut de la figure, au-dessus de la valeur entre crochet représentant le nombre de données affichées. À cet endroit peut aussi figurer la mention "END" lorsque le tracer a reçu une fin de fichier.

Les lignes de texte sont lues en dissociant chaque mot séparé par un ou plusieurs espace(s). Chaque série à tracer doit alors coïncider avec un indice de colonne ainsi formée. Si une ligne ne présente pas de valeur numérique à l'une des colonnes devant correspondre à une série, elle sera ignorée. Par défaut les lignes ignorées sont réécrites sur la sortie standard et celles traitées sont tues. Ce comportement peut être changé à l'aide des options `-q, --quiet` et `-p, --pass`.


**Les Principales options :**

* La lecture depuis un fichier se fait avec l'option `-f, --file` suivit du chemin vers le fichier. Dans le cas contraire, le traceur lit depuis l'entrée standard.
* L'option `--sep` permet de spécifier le caractère qui sépare chaque valeur sur une ligne. Par défaut, il s'agit des espaces. Pour lire un fichier CSV, il faudra donc préciser `--sep=,`.
* L'option `-C, --columns` permet de spécifier les colonnes correspondant aux séries à tracer. Le numéro des colonnes sont à séparer par des virgules pour que les séries soient tracées sur un même graphique ou par un slash pour qu'elles soient réparties sur des graphiques superposés.
* L'option `-a, --abscissa` fait passer la première série en abscisse pour toutes les autres.
* L'option `-b, --band` permet de définir une bande glissante de valeurs à afficher lors de la lecture sur l'entrée standard ou le nombre de données après lesquelles s'arrêter lors de la lecture à partir d'un fichier. Le deuxième cas est particulièrement utile en combinaison avec l'option `-o, --offset` pour sélectionner une plage de valeurs à tracer.
* Les courbes peuvent être misent en forme via les options `-c, --colors`, `-d, --dashed`, `-t, --dotted`, `-m, --mixed` ou encore `-w, --linewidth`.
* La figure peut être légendée grâce aux options `-L, --labels`, `-A, --xlabel` et `-T, --titles`.
* L'option `-P, --plain` impose l'utilisation du noir et du blanc pour les décorations de la figure afin par exemple d'exporter celle-ci.
* L'ensemble des options est visible à l'aide de `-h, --help`.


**Quelques exemples d'utilisation :**

`$ ./tracer.py`

*Lira tout ce qui vient de l'entrée standard (à utiliser alors avec un tube). La première ligne reçue comprenant au moins une valeur numérique séparée par des espaces déterminera la ou les série(s) à tracer sur un même graphique.*

`$ ./tracer.py -C 2,3,5`

*Traitera les lignes où les colonnes 2, 3 et 5 sont des valeurs numériques et tracera les trois séries sur un même graphique.*

`$ ./tracer.py -C 2,3/5`

*Tracera les séries issues des colonnes 2 et 3 sur un premier graphique et celle issue de la colonne 5 sur un autre partageant la même abscisse.*

`$ ./tracer.py -C 2,3/5 -a`

*Tracera les séries issues des colonnes 3 et 5 sur deux graphiques différents mais tous deux en fonction de la première série spécifiée, c'est-à-dire ici celle issue de la deuxième colonne.*

`$ ./tracer.py -f file.txt -o 1000 -b 200`

*Trace la ou les série(s) de valeurs numériques contenues dans le fichier file.txt entre la 1000ème et la 1200ème donnée.*

`$ ./tracer.py -f file.txt -n 2 -L '$\alpha$,$\beta$' -T Résultats -P -S`

*Traite les lignes du fichier file.txt comportant exactement 2 colonnes et légende la première série par la lettre grecque alpha et la deuxième par la lettre grecque beta. Le graphique est intitulé "Résultats", les couleurs sont claires et les marges transparentes afin que la figure soit propre à l'exportation.*

`$ ./tracer.py -aC1,2 -x25 -s50x100 -p | ./tracer.py -aC3,4 -x75 -s50x100`

*Tracera dans une première fenêtre occupant la moitiée gauche de l'écran la série issue de la deuxième colonne en fonction de celle issue de la première colonne et dans une seconde fenêtre occupant la moitiée droite de l'écran la série issue de la quatrième colonne en fonction de celle issue de la troisième colonne.*


**La barre d'outils :**

La barre d'outils custom dispose, en plus des boutons de l'interface standard de matplotlib, de trois boutons supplémentaires lorsque le traceur lit depuis un tube ou un socket :
* Un bouton "change band/rate" pour changer le nombre de données maximum à afficher ou la période d'affichage. Double-cliquer sur ce bouton ouvre une fenêtre permettant de renseigner directement la valeur désirée pour chacun d'eux. Sinon leur valeur peut être changée en cliquant-glissant de haut en bas dans un graphique, respectivement avec le bouton gauche ou avec le bouton droit de la souris. Le raccourci clavier associé est `b`.
* Un bouton "pause" pour stopper l'actualisation des courbes. En appuyant à nouveau, l'affichage reprend aux données actuelles. Le raccourci clavier associé est `p` ou `espace`.
* Un bouton "save data" pour extraire les données actuellement affichées et les enregistrer dans un fichier texte, une série par colonne, dans l'ordre dans lequel elles ont été spécifiée. Le raccourci clavier associé est `d`.
