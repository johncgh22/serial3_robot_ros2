# serial3_robot_ros2

Migración a **ROS 2 Lyrical** (Ubuntu 26.04) del robot serial de 3 GDL de [serial3_robot_v3](https://github.com/johncgh22/serial3_robot_v3) (ROS Noetic), con simulación en **Gazebo Sim** y control con **ros2_control**.

## Estado

| Fase | Paquetes | Estado |
|---|---|---|
| 1. Descripción del robot y RViz2 | `serial3_description` | ✅ Disponible |
| 2. Controladores y simulación en Gazebo Sim | `serial3_bringup`, `serial3_gazebo` | ✅ Disponible |
| 3. Robot físico | `serial3_hardware` | Pendiente |

## 1. Requisitos

- Ubuntu 26.04 con [ROS 2 Lyrical](https://docs.ros.org/en/lyrical/Installation.html) (`ros-lyrical-desktop`)
- Herramientas de compilación, control y simulación:

  ~~~bash
  sudo apt install python3-colcon-common-extensions python3-rosdep \
    ros-lyrical-xacro ros-lyrical-joint-state-publisher-gui \
    ros-lyrical-ros2-control ros-lyrical-ros2-controllers \
    ros-lyrical-ros-gz ros-lyrical-gz-ros2-control
  ~~~

## 2. Instalación

1. Crea un workspace y clona el repositorio:

   ~~~bash
   mkdir -p ~/ros2_ws/src
   cd ~/ros2_ws/src
   git clone <url-de-este-repositorio> serial3_robot_ros2
   ~~~

2. Instala las dependencias que falten con rosdep:

   ~~~bash
   cd ~/ros2_ws
   sudo rosdep init   # solo la primera vez
   rosdep update
   rosdep install --from-paths src --ignore-src -y
   ~~~

3. Compila y carga el entorno:

   ~~~bash
   source /opt/ros/lyrical/setup.bash
   colcon build --symlink-install
   source install/setup.bash
   ~~~

   Para no repetirlo en cada terminal nueva:

   ~~~bash
   echo "source /opt/ros/lyrical/setup.bash" >> ~/.bashrc
   echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
   ~~~

4. (Opcional) Comprueba que el modelo es válido:

   ~~~bash
   colcon test --packages-select serial3_description
   colcon test-result --verbose
   ~~~

## 3. Visualizar el robot en RViz2

~~~bash
ros2 launch serial3_description display.launch.py
~~~

Se abre RViz2 con el modelo y una ventana de deslizadores para mover cada junta (±90°). Sirve para revisar el modelo sin simular física.

| Argumento | Valor por defecto | Descripción |
|---|---|---|
| `gui` | `true` | Muestra los deslizadores. Con `false` las juntas quedan en 0 |
| `model` | `urdf/serial3.urdf.xacro` | Archivo Xacro/URDF a cargar |
| `rviz_config` | `rviz/serial3.rviz` | Configuración de RViz2 |

## 4. Simular el robot en Gazebo Sim

1. Lanza la simulación:

   ~~~bash
   ros2 launch serial3_bringup sim.launch.py
   ~~~

   Este archivo abre Gazebo con un mundo vacío, coloca el robot con las juntas en 0 rad y arranca dos controladores:
   - `joint_state_broadcaster`: publica `/joint_states`.
   - `arm_controller` (`JointTrajectoryController`): sigue trayectorias mandando **esfuerzo** a cada junta con un PID.

   | Argumento | Valor por defecto | Descripción |
   |---|---|---|
   | `gui` | `true` | Muestra la ventana de Gazebo. Con `false` solo corre el servidor |
   | `rviz` | `false` | Abre también RViz2 |
   | `world` | `serial3_gazebo/worlds/serial3_empty.sdf` | Mundo SDF a cargar |

2. En otra terminal, comprueba que los controladores estén activos:

   ~~~bash
   ros2 control list_controllers
   ~~~

   Deben aparecer `joint_state_broadcaster` y `arm_controller` como `active`.

3. Mueve el robot enviando una trayectoria (posiciones en radianes, entre -1.5708 y 1.5708):

   ~~~bash
   ros2 action send_goal /arm_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory \
     "{trajectory: {joint_names: [base_to_e1_joint, e1_to_e2_joint, e2_to_e3_joint],
       points: [{positions: [0.5, -0.8, 1.0], time_from_start: {sec: 2}}]}}"
   ~~~

   Debe terminar con `Goal finished with status: SUCCEEDED`.

   > **Importante:** elige `time_from_start` de modo que ninguna junta supere su velocidad máxima (tabla de la sección 6). El controlador no lo comprueba, pero Gazebo sí aplica el límite. Si la trayectoria es demasiado rápida, la junta se queda atrás y el objetivo termina en `ABORTED` ("path tolerance violation"). Como referencia, para recorrer todo el rango (3 rad) usa al menos 4 s.

4. Observa la respuesta de las juntas:

   ~~~bash
   ros2 topic echo /joint_states
   ros2 topic echo /arm_controller/controller_state   # referencia, posición real y error
   ~~~

   También puedes graficarlas con `ros2 run rqt_plot rqt_plot`.

### Probar sin Gazebo (hardware mock)

Para revisar controladores y trayectorias sin física:

~~~bash
ros2 launch serial3_bringup mock.launch.py
~~~

El hardware mock copia el mando directamente al estado, así que en este modo `arm_controller` manda **posición** en lugar de esfuerzo. El cambio está en [serial3_controllers_mock.yaml](serial3_bringup/config/serial3_controllers_mock.yaml). Los comandos de la sección 4 funcionan igual.

### Ajustar las ganancias PID

Las ganancias están en [serial3_controllers.yaml](serial3_bringup/config/serial3_controllers.yaml), en `arm_controller.gains`. Los valores actuales (p = 100, i = 0.01, d = 0.01 para las tres juntas) siguen trayectorias con un error menor a 0.01 rad. Para probar otros valores con la simulación en marcha:

~~~bash
ros2 param set /arm_controller gains.e1_to_e2_joint.p 150.0
~~~

Cuando encuentres valores adecuados, cópialos al YAML.

## 5. Estructura

~~~
serial3_robot_ros2/
├── serial3_description/
│   ├── urdf/
│   │   ├── serial3.urdf.xacro           # Modelo del robot (único archivo a editar)
│   │   ├── serial3.ros2_control.xacro   # Interfaces de las juntas y plugin de Gazebo
│   │   └── materials.xacro              # Colores
│   ├── meshes/{visual,collision}/       # Mallas STL
│   ├── rviz/serial3.rviz
│   └── launch/display.launch.py
├── serial3_bringup/
│   ├── config/
│   │   ├── serial3_controllers.yaml       # Controladores y ganancias PID
│   │   └── serial3_controllers_mock.yaml  # Cambios para el hardware mock
│   └── launch/
│       ├── sim.launch.py                  # Gazebo Sim + controladores
│       └── mock.launch.py                 # ros2_control sin simulador
└── serial3_gazebo/
    └── worlds/serial3_empty.sdf           # Mundo vacío (paso de 1 ms)
~~~

El Xacro acepta dos argumentos:
- `hw:=mock|gazebo|real`: elige el hardware de ros2_control. `real` es para la fase 3 y todavía no funciona.
- `controllers_file:=<ruta>`: YAML de controladores que carga Gazebo. Solo se usa con `hw:=gazebo`.

Para ver el URDF generado:

~~~bash
xacro $(ros2 pkg prefix --share serial3_description)/urdf/serial3.urdf.xacro hw:=gazebo
~~~

## 6. Juntas

| Junta | Une | Esfuerzo máx. | Velocidad máx. |
|---|---|---|---|
| `base_to_e1_joint` | `base_link` → `e1_link` | 77 N·m | 1.43 rad/s |
| `e1_to_e2_joint` | `e1_link` → `e2_link` | 133 N·m | 1.29 rad/s |
| `e2_to_e3_joint` | `e2_link` → `e3_link` | 66 N·m | 2.13 rad/s |

Todas tienen un rango de ±90° (±1.5708 rad). `base_link` está fijo a `world` y `end_effector` está fijo a `e3_link`.

## 7. Solución de problemas

| Problema | Posible causa / solución |
|---|---|
| `Package 'serial3_bringup' not found` | No hiciste `source install/setup.bash` en esa terminal. |
| El objetivo termina en `ABORTED` ("path tolerance violation") | La trayectoria supera la velocidad máxima de alguna junta. Aumenta `time_from_start`. |
| El spawner dice `Controller already loaded` o `Failed to activate` | Hay otra simulación o `mock.launch.py` corriendo. Ciérrala antes de lanzar de nuevo. |
| `Could not enable FIFO RT scheduling policy` | Solo es un aviso: el usuario no tiene permisos de tiempo real. No afecta la simulación. |
| `libEGL warning: egl: failed to create dri2 screen` | Aviso del controlador gráfico. Gazebo funciona igual. |
| RViz2 no muestra el robot | En *Global Options*, pon `Fixed Frame` en `world`. |

## Cambios respecto a la versión de ROS 1

- El paquete `serial3_robot_v3` se dividió en `serial3_description`, `serial3_bringup` y `serial3_gazebo`.
- El robot se llama `serial3` y la junta fija de la base se llama `world_to_base_joint`.
- Las `<transmission>` se sustituyeron por un bloque `<ros2_control>`, y `gazebo_ros_control` por `gz_ros2_control`.
- Los tres `effort_controllers/JointPositionController` se sustituyeron por un solo `JointTrajectoryController` que manda esfuerzo con un PID por junta. Las ganancias se reajustaron para Gazebo Sim: con p = 1, las juntas 1 y 3 no podían seguir la trayectoria.
- `gazebo_pid.yaml` ya no hace falta.
- El mundo `serial3_w1` de ROS 1 tenía una copia del robot con rutas absolutas de otra computadora. Se sustituyó por `serial3_empty.sdf`, con los mismos parámetros físicos.
- El URDF ya no se guarda en el repositorio: se genera desde el Xacro al lanzar.
