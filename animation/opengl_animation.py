import os
import glfw
import logging
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
import numpy as np


logger = logging.getLogger(__name__)

class StateTransition:
    def __init__(self, name, color_start, color_end=None, transition_duration=3.0):
        self.name = name
        self.color_start = color_start
        self.color_end = color_end or (0, 0, 0)
        self.transition_duration = transition_duration
        self.is_enabled = False
        self.transition_start_time = 0
        self.transitioning = False
        self.transition_direction = 1  # 1 for fade in, -1 for fade out

    def get_current_color(self, current_time):
        if not self.transitioning:
            return self.color_start if self.is_enabled else self.color_end
        
        progress = min((current_time - self.transition_start_time) / self.transition_duration, 1.0)
        if self.transition_direction < 0:
            progress = 1.0 - progress
        
        return tuple(
            start + (end - start) * progress
            for start, end in zip(
                self.color_end if self.transition_direction < 0 else self.color_start,
                self.color_start if self.transition_direction < 0 else self.color_end
            )
        )

class OpenGLAnimation:
    def __init__(self):
        self.transitions = {
            "waiting": StateTransition("waiting", (0.0, 0.0, 1.0)),
            "listening": StateTransition("listening", (1.0, 0.0, 0.0)),
            "speaking": StateTransition("speaking", (0.0, 1.0, 0.0)),
            "thinking": StateTransition("thinking", (1.0, 1.0, 1.0))
        }
        # self.transitions["waiting"].is_enabled = True  # Set waiting as default state
        self.running = False
        self.shader_program = None
        self.start_time = time.time()
        self.window = None
        self.vao = None
        self.vbo = None

    def load_shaders(self):
        def compile_shader(source, shader_type):
            shader = glCreateShader(shader_type)
            glShaderSource(shader, source)
            glCompileShader(shader)

            if not glGetShaderiv(shader, GL_COMPILE_STATUS):
                error = glGetShaderInfoLog(shader).decode()
                raise Exception(f"Shader compilation error:\n{error}")
            else:
                print(
                    f"Shader ({'vertex' if shader_type == GL_VERTEX_SHADER else 'fragment'}) compiled successfully")

            return shader

        def link_program(vertex_shader, fragment_shader):
            program = glCreateProgram()
            glAttachShader(program, vertex_shader)
            glAttachShader(program, fragment_shader)
            glLinkProgram(program)

            if not glGetProgramiv(program, GL_LINK_STATUS):
                error = glGetProgramInfoLog(program).decode()
                raise Exception(f"Shader program linking error:\n{error}")
            else:
                print("Shader program linked successfully")

            return program

        script_dir = os.path.dirname(os.path.abspath(__file__))

        vertex_shader_path = os.path.join(script_dir, "vertex_shader.glsl")
        with open(vertex_shader_path, "r") as f:
            vertex_shader_source = f.read()
        vertex_shader = compile_shader(vertex_shader_source, GL_VERTEX_SHADER)

        fragment_shader_path = os.path.join(script_dir, "fragment_shader.glsl")
        with open(fragment_shader_path, "r") as f:
            fragment_shader_source = f.read()
        fragment_shader = compile_shader(
            fragment_shader_source, GL_FRAGMENT_SHADER)

        self.shader_program = link_program(vertex_shader, fragment_shader)
        print("Shader Program ID:", self.shader_program)

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

    def start(self):
        if not glfw.init():
            raise Exception("GLFW initialization failed")

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        self.window = glfw.create_window(
            800, 600, "Sphere Animation", None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("GLFW window creation failed")

        glfw.make_context_current(self.window)

        print("OpenGL Version:", glGetString(GL_VERSION))
        print("OpenGL Vendor:", glGetString(GL_VENDOR))
        print("OpenGL Renderer:", glGetString(GL_RENDERER))

        self.load_shaders()

        # Set up VAO and VBO
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        vertices = np.array([
            -1.0, -1.0, 0.0,
            1.0, -1.0, 0.0,
            1.0,  1.0, 0.0,
            -1.0,  1.0, 0.0
        ], dtype=np.float32)

        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes,
                     vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                              3 * sizeof(GLfloat), None)
        glEnableVertexAttribArray(0)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        glUseProgram(self.shader_program)
        glUniform2f(glGetUniformLocation(
            self.shader_program, "iResolution"), 800, 600)

        self.running = True

    def render(self):
        if not self.running or glfw.window_should_close(self.window):
            return False

        current_time = time.time()
        glfw.poll_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_program)

        # Update transitions and send to shader
        other_states_active = False
        for i, (name, transition) in enumerate(self.transitions.items()):
            if name != "waiting" and transition.is_enabled:
                other_states_active = True

            if transition.transitioning:
                color = transition.get_current_color(current_time)
                progress = (current_time - transition.transition_start_time) / transition.transition_duration
                if progress >= 1.0:
                    transition.transitioning = False
            else:
                color = transition.get_current_color(current_time)

            # For waiting state, only enable if no other states are active
            is_enabled = transition.is_enabled
            if name == "waiting":
                is_enabled = is_enabled and not other_states_active

            base_uniform = f"states[{i}]"
            glUniform1i(glGetUniformLocation(self.shader_program, f"{base_uniform}.enabled"), is_enabled)
            glUniform3f(glGetUniformLocation(self.shader_program, f"{base_uniform}.color"), *color)

        glUniform1f(glGetUniformLocation(self.shader_program, "iTime"), current_time - self.start_time)
        
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        glBindVertexArray(0)

        glfw.swap_buffers(self.window)
        return True

    def set_state(self, state_name, value):
        """
        Set the state of a specific animation layer.
        Each state is managed independently without affecting others.
        
        Args:
            state_name (str): Name of the state to modify
            value (bool): New value for the state
        """
        transition = self.transitions[state_name]
        if transition.is_enabled != value:
            current_time = time.time()
            transition.is_enabled = value
            transition.transition_start_time = current_time
            transition.transitioning = True
            transition.transition_direction = 1 if value else -1
            
            # Handle waiting state
            if state_name != "waiting":
                any_active = any(t.is_enabled for name, t in self.transitions.items() if name != "waiting")
                waiting_transition = self.transitions["waiting"]
                if any_active and waiting_transition.is_enabled:
                    waiting_transition.is_enabled = False
                    waiting_transition.transition_start_time = current_time
                    waiting_transition.transitioning = True
                    waiting_transition.transition_direction = -1
                elif not any_active and not waiting_transition.is_enabled:
                    waiting_transition.is_enabled = True
                    waiting_transition.transition_start_time = current_time
                    waiting_transition.transitioning = True
                    waiting_transition.transition_direction = 1
            
            logger.info(f"OpenGL Animation State change - {state_name}: {value}")
        

    def stop(self):
        self.running = False
        if self.window:
            glfw.destroy_window(self.window)
        glfw.terminate()
