import json
import itertools
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors # Importar para ListedColormap

# --- 1. Data Loading and Preprocessing ---
# Este apartado se encarga de cargar los datos de asignaciones de alumnos y profesores
# desde los archivos JSON especificados.
# También corrige posibles errores tipográficos en los nombres de los cursos para asegurar
# la consistencia de los datos.

# Cargar las asignaciones de alumnos desde 'asignaciones_alumnos.json'
with open('asignaciones_alumnos.json', 'r') as f:
    student_assignments = json.load(f)

# Cargar las asignaciones de profesores desde 'asignaciones_profesores.json'
with open('asignaciones_profesores.json', 'r') as f:
    professor_assignments = json.load(f)

# Corrección de un error tipográfico común en el nombre del curso
# 'ntroducción a ciencia de la computación' a 'Introducción a ciencia de la computación'
# para mantener la coherencia de los datos.
corrected_student_assignments = {}
for student, courses in student_assignments.items():
    corrected_courses = [
        'Introducción a ciencia de la computación' if course == 'ntroducción a ciencia de la computación' else course
        for course in courses
    ]
    corrected_student_assignments[student] = corrected_courses
student_assignments = corrected_student_assignments

# Identificar todos los cursos únicos presentes en las asignaciones de alumnos y profesores.
all_courses = set()
for courses in student_assignments.values():
    all_courses.update(courses)
for courses in professor_assignments.values():
    all_courses.update(courses)

# --- 2. Generación del Grafo de Conflictos ---
# Esta sección construye el 'grafo de conflictos'. En este grafo, cada nodo representa un curso,
# y una arista entre dos nodos indica que existe un conflicto de programación, lo que significa
# que los exámenes de esos dos cursos no pueden realizarse simultáneamente.
# Los conflictos surgen si:
#   - Un alumno está inscrito en ambos cursos.
#   - El mismo profesor imparte ambos cursos.

# Inicializar conjuntos para almacenar las aristas de conflicto de alumnos y profesores.
student_conflict_graph_edges = set()
professor_conflict_graph_edges = set()

# Generar conflictos por alumnos: Si un alumno cursa dos materias, estas entran en conflicto.
for student, courses in student_assignments.items():
    # Usar itertools.combinations para obtener todas las parejas únicas de cursos por cada alumno.
    for course1, course2 in itertools.combinations(courses, 2):
        # Almacenar las aristas como frozensets para asegurar que sean únicas,
        # sin importar el orden de los cursos (ej. {A,B} es lo mismo que {B,A}).
        student_conflict_graph_edges.add(frozenset({course1, course2}))

# Generar conflictos por profesores: Si un profesor imparte dos materias, estas entran en conflicto.
for professor, courses in professor_assignments.items():
    # Usar itertools.combinations para obtener todas las parejas únicas de cursos por cada profesor.
    for course1, course2 in itertools.combinations(courses, 2):
        # Almacenar las aristas como frozensets para asegurar que sean únicas.
        professor_conflict_graph_edges.add(frozenset({course1, course2}))

# Combinar ambos conjuntos de conflictos para formar el conjunto final de aristas del grafo de conflictos.
combined_conflict_graph_edges = student_conflict_graph_edges.union(professor_conflict_graph_edges)

# Crear un objeto de grafo utilizando la librería NetworkX.
G = nx.Graph()

# Añadir todos los cursos únicos como nodos al grafo.
G.add_nodes_from(all_courses)

# Añadir las aristas de conflicto al grafo.
for edge in combined_conflict_graph_edges:
    course1, course2 = tuple(edge)
    G.add_edge(course1, course2)

# --- 3. Coloración del Grafo para Asignación de Franjas Horarias ---
# Esta sección aplica un algoritmo de coloración de grafos (heurística de Welsh-Powell)
# para asignar franjas horarias (colores) a los cursos.
# El objetivo es minimizar el número de franjas horarias utilizadas, asegurando
# que no haya conflictos de programación.

# Ordenar los nodos (cursos) por su grado (número de conflictos) en orden descendente.
# Esta heurística ayuda a obtener una mejor coloración con algoritmos golosos.
sorted_nodes = sorted(G.nodes(), key=lambda node: G.degree[node], reverse=True)

# Diccionario para almacenar la franja horaria (color) asignada a cada curso.
coloring = {}
# Conjunto para llevar un registro de los colores usados por los nodos vecinos
# durante el proceso de asignación.
used_neighbor_colors = set()

# Iterar a través de los nodos ordenados y asignar el color disponible más pequeño.
for node in sorted_nodes:
    used_neighbor_colors.clear() # Limpiar para cada nuevo nodo

    # Recopilar los colores de los vecinos que ya han sido coloreados.
    for neighbor in G.neighbors(node):
        if neighbor in coloring:
            used_neighbor_colors.add(coloring[neighbor])

    # Encontrar el entero positivo más pequeño (color/franja horaria) que no esté
    # siendo usado por ningún vecino.
    color = 1
    while color in used_neighbor_colors:
        color += 1
    coloring[node] = color

# Agrupar los cursos por su franja horaria asignada.
schedule = {}
for course, time_slot in coloring.items():
    if time_slot not in schedule:
        schedule[time_slot] = []
    schedule[time_slot].append(course)

# --- 4. Asignación de Aulas y Generación del Horario ---
# Esta sección determina la cantidad mínima de aulas necesarias y las asigna.
# Las aulas pueden ser reutilizadas en diferentes franjas horarias.

# Calcular el número máximo de exámenes simultáneos en cualquier franja horaria.
# Este valor representa la cantidad mínima de aulas requeridas.
max_simultaneous_exams = 0
for time_slot, courses_in_slot in schedule.items():
    max_simultaneous_exams = max(max_simultaneous_exams, len(courses_in_slot))

# Asignar un aula única a cada examen dentro de cada franja horaria.
room_assignments = {}
for time_slot, courses_in_slot in schedule.items():
    room_assignments[time_slot] = {}
    for i, course in enumerate(courses_in_slot):
        room_assignments[time_slot][course] = f"Aula {i + 1}"

# --- 5. Visualización del Grafo y Salida del Horario ---
# Esta sección genera una visualización del grafo de conflictos, donde los nodos
# están coloreados según sus franjas horarias asignadas.
# También imprime el horario detallado de los exámenes.

print("--- Horario de Exámenes ---")
for time_slot in sorted(schedule.keys()):
    print(f"\nFranja Horaria {time_slot}:")
    for course in schedule[time_slot]:
        room = room_assignments[time_slot][course]
        print(f"  - {course} (Aula Asignada: {room})")

print(f"\nCantidad mínima de aulas requeridas: {max_simultaneous_exams}")

# Configuración de la visualización
plt.figure(figsize=(15, 10))
# Utilizar un diseño de resorte para una mejor distribución visual de los nodos.
pos = nx.spring_layout(G, k=0.8, iterations=50)

# Generar colores para los nodos basados en sus franjas horarias asignadas.
# Se utiliza un mapa de colores ('tab10') para obtener colores distintos para cada franja horaria.
num_time_slots = max(coloring.values())

# CORRECCIÓN: Obtener el colormap base y luego crear un ListedColormap para la cantidad exacta de franjas.
colors_map_base = plt.colormaps['tab10']
# Asegurarse de que num_time_slots no exceda los colores disponibles en 'tab10' (10 colores).
# Si num_time_slots fuera mayor, se necesitaría un colormap diferente o una lógica para reutilizar/generar más colores.
# Dado el problema, es probable que num_time_slots sea <= 10.
colors_map = mcolors.ListedColormap([colors_map_base(i) for i in range(num_time_slots)])


# Dibujar los nodos del grafo.
nx.draw_networkx_nodes(G, pos, node_color=[colors_map(coloring[node] - 1) for node in G.nodes()], node_size=3000)
# Dibujar las aristas del grafo.
nx.draw_networkx_edges(G, pos, edge_color='gray', alpha=0.5)
# Dibujar las etiquetas (nombres de los cursos) en los nodos.
nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

# Crear una leyenda para asociar los colores con las franjas horarias.
legend_labels = {f'Franja Horaria {i+1}': colors_map(i) for i in range(num_time_slots)}
patches = [plt.Line2D([0], [0], marker='o', color='w', label=label,
                      markerfacecolor=color, markersize=10) for label, color in legend_labels.items()]
plt.legend(handles=patches, title="Franjas Horarias", bbox_to_anchor=(1.05, 1), loc='upper left')

plt.title("Grafo de Conflictos con Cursos Coloreados por Franjas Horarias Asignadas")
plt.axis('off') # Ocultar los ejes
plt.tight_layout() # Ajustar el diseño para evitar que las etiquetas se superpongan
plt.show()
