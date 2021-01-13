#!/usr/bin/env python3
import glfw
import OpenGL.GL as gl
import imgui
import os

from array import array
from math import sin

from imgui.integrations.glfw import GlfwRenderer

from modules import logger
from modules import filewatch
from modules import netwatch
from modules import sshwatch

modules = {}


def main():
    imgui.create_context()
    window = impl_glfw_init()
    impl = GlfwRenderer(window)

    modules['file_watch'] = filewatch.FileWatch()

    modules['nettraf_watch'] = netwatch.NetWatch()

    modules['ssh_watch'] = sshwatch.SSHWatch()

    logg = logger.Logger()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        style = imgui.get_style()

        style.window_rounding = 0

        imgui.new_frame()

        style.frame_rounding = 0

        flags = imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_TITLE_BAR

        imgui.set_next_window_size(1220, 706)
        imgui.set_next_window_position(0, 0)
        imgui.begin("LinuxTKS", False, flags=flags)

        imgui.begin_child("left_bottom", width=350, height=250)
        imgui.text("Modules")
        imgui.separator()
        imgui.spacing()

        for moduleName, module in modules.items():
            opened, test_visisble = imgui.collapsing_header(module.name)
            if opened:
                module.configurationInterface()

        imgui.end_child()

        imgui.same_line()

        imgui.begin_child("console", height=250)
        imgui.text("General Logs")

        imgui.spacing()

        imgui.begin_child("logger", border=True)

        for message in logg.getLogs():
            color = (255, 255, 255, 255)

            if "ERROR" in message:
                imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0)

            if "ALERT" in message:
                imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)

            imgui.push_text_wrap_position()
            imgui.text_wrapped(message)

            if "ERROR" in message or "ALERT" in message:
                imgui.pop_style_color(1)

        imgui.end_child()
        imgui.end_child()

        imgui.spacing()

        imgui.begin_child("module_views")
        imgui.text("Module Interfaces")
        imgui.separator()

        flags = imgui.WINDOW_MENU_BAR

        imgui.begin_child("module_selector", height=19, flags=flags)
        if (imgui.begin_menu_bar()):
            for moduleName, module in modules.items():
                module.moduleMenuBar(modules)
                    

            # imgui.same_line()
            imgui.end_menu_bar()
        imgui.end_child()

        imgui.separator()

        for moduleName, module in modules.items():
            if module.started and module.interfaceActive:
                module.displayInterface()
        imgui.end_child()

        imgui.end()

        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()
    
    for moduleName, module in modules.items():
        if module.started:
            module.stop()


def impl_glfw_init():
    width, height = 1220, 706
    window_name = "LinuxTKS"

    if not glfw.init():
        printToLog("Could not initialize OpenGL context")
        exit(1)


    glfw.window_hint(glfw.RESIZABLE, False)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(
        int(width), int(height), window_name, None, None
    )
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        printToLog("Could not initialize Window")
        exit(1)

    return window


if __name__ == "__main__":
    main()