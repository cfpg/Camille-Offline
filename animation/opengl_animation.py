import os
import glfw
from OpenGL.GL import *
from OpenGL.GL.shaders import compileProgram, compileShader
import time
import numpy as np


class OpenGLAnimation:
    def __init__(self):
        self.state = 0  # 0 = waiting, 1 = listening, 2 = talking
        self.running = False
        self.shader_program = None
        self.start_time = time.time()
        self.last_state_change = time.time()  # Add this line
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

        glfw.poll_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glUseProgram(self.shader_program)

        # Set shader uniforms
        glUniform1f(glGetUniformLocation(self.shader_program,
                    "iTime"), time.time() - self.start_time)
        glUniform1i(glGetUniformLocation(
            self.shader_program, "state"), self.state)
        # Add this line to pass transition time to shader
        glUniform1f(glGetUniformLocation(self.shader_program,
                    "transitionTime"), time.time() - self.last_state_change)

        # Draw the full-screen quad
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)
        glBindVertexArray(0)

        glfw.swap_buffers(self.window)
        return True

    def set_state(self, state):
        if self.state != state:  # Only update if state actually changes
            self.last_state_change = time.time()
            self.state = state

    def stop(self):
        self.running = False
        if self.window:
            glfw.destroy_window(self.window)
        glfw.terminate()
