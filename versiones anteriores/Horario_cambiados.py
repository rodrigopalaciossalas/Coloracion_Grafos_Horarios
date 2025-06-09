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

# Cargar las asignaciones de profesores desde 'asignaciones_profesores.json', si existe
# Se añade un manejo de error para el caso de que el archivo no exista
try:
    with open('asignaciones_profesores.json', 'r') as f:
        professor_assignments = json.load(f)
except FileNotFoundError:
    print("Advertencia: 'asignaciones_profesores.json' no encontrado. Los conflictos de profesores no se considerarán.")
    professor_assignments = {} # Inicializar como diccionario vacío si el archivo no existe


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

# Guardar las aristas combinadas para diferenciarlas después
# Las aristas de profesor son un subconjunto de las combinadas
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
num_time_slots = max(coloring.values())
colors_map_base = plt.colormaps['tab10']
colors_map = mcolors.ListedColormap([colors_map_base(i) for i in range(num_time_slots)])

# --- Dibujar las aristas con diferentes grosores ---
# Separar las aristas de conflicto por estudiantes y profesores
student_only_edges = [tuple(edge) for edge in student_conflict_graph_edges if edge not in professor_conflict_graph_edges]
professor_edges = [tuple(edge) for edge in professor_conflict_graph_edges]
shared_edges = [tuple(edge) for edge in student_conflict_graph_edges if edge in professor_conflict_graph_edges]

# Dibujar aristas de estudiantes (más finas)
nx.draw_networkx_edges(G, pos, edgelist=student_only_edges, edge_color='skyblue', width=1.0, alpha=0.5, label='Conflicto Alumno')
# Dibujar aristas de profesores (más gruesas)
nx.draw_networkx_edges(G, pos, edgelist=professor_edges, edge_color='red', width=3.0, alpha=0.7, label='Conflicto Profesor')
# Dibujar aristas compartidas (aún más gruesas, o con un color diferente)
# Aquí las haremos del color de profesor para simplificar y darles el grosor de profesor
nx.draw_networkx_edges(G, pos, edgelist=shared_edges, edge_color='darkred', width=3.5, alpha=0.8, label='Conflicto Ambos')


# Dibujar los nodos del grafo.
nx.draw_networkx_nodes(G, pos, node_color=[colors_map(coloring[node] - 1) for node in G.nodes()], node_size=3000)
# Dibujar las etiquetas (nombres de los cursos) en los nodos.
nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')

# Crear una leyenda para asociar los colores con las franjas horarias.
legend_labels = {f'Franja Horaria {i+1}': colors_map(i) for i in range(num_time_slots)}
patches_colors = [plt.Line2D([0], [0], marker='o', color='w', label=label,
                            markerfacecolor=color, markersize=10) for label, color in legend_labels.items()]

# Crear handles para la leyenda de las aristas
edge_legend_student = plt.Line2D([0], [0], color='skyblue', lw=1.0, label='Conflicto Alumno')
edge_legend_professor = plt.Line2D([0], [0], color='red', lw=3.0, label='Conflicto Profesor')
edge_legend_shared = plt.Line2D([0], [0], color='darkred', lw=3.5, label='Conflicto Ambos')


# Combinar todos los handles para la leyenda
all_patches = patches_colors + [edge_legend_student, edge_legend_professor, edge_legend_shared]

# --- Cambiar la ubicación de la leyenda ---
# bbox_to_anchor=(0.5, -0.15) y loc='upper center' suelen ponerla abajo centrada.
# Puedes ajustar el valor '-0.15' para moverla más arriba o más abajo.
plt.legend(handles=all_patches, title="Leyenda", bbox_to_anchor=(0.5, -0.15), loc='upper center', ncol=2)


plt.title("Grafo de Conflictos con Cursos Coloreados por Franjas Horarias Asignadas")
plt.axis('off') # Ocultar los ejes
plt.tight_layout(rect=[0, 0.1, 1, 1]) # Ajustar el diseño para dar espacio a la leyenda inferior
plt.show()