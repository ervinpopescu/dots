from libqtile import qtile
from libqtile.backend.base.window import Window
from libqtile.core.manager import Qtile
from libqtile.lazy import lazy
from libqtile.log_utils import logger
from qtile_extras.popup.toolkit import PopupRelativeLayout, PopupText

from modules.settings import colors, settings

qtile: Qtile

## Working!
# @lazy.window.function
# def close_app_with_warning_window(window):
#     layout = PopupRelativeLayout(
#         qtile,
#         width=1000,
#         height=400,
#         opacity=0.9,
#         background=colors["darkblue"],
#         initial_focus=None,
#         close_on_click=False,
#     )

#     def double_kill():
#         window.kill()
#         layout.kill()

#     controls = [
#         PopupText(
#             font=settings["text_font"],
#             pos_x=1 / 20,
#             pos_y=1 / 8,
#             width=0.9,
#             height=1 / 4,
#             fontsize=28,
#             foreground="000000",
#             text=f"You sure you want to kill window\n{window.name}?",
#             h_align="center",
#             v_align="middle",
#             wrap=True,
#         ),
#         PopupText(
#             font=settings["text_font"],
#             pos_x=1 / 3 - 0.1,
#             pos_y=2 / 3,
#             width=0.1,
#             height=0.1,
#             fontsize=28,
#             foreground="000000",
#             text="Yes",
#             h_align="center",
#             v_align="middle",
#             wrap=True,
#             mouse_callbacks={
#                 "Button1": double_kill,
#             },
#         ),
#         PopupText(
#             font=settings["text_font"],
#             pos_x=2 / 3,
#             pos_y=2 / 3,
#             width=0.1,
#             height=0.1,
#             fontsize=28,
#             foreground="000000",
#             text="No",
#             h_align="center",
#             v_align="middle",
#             wrap=True,
#             mouse_callbacks={"Button1": layout.kill},
#         ),
#     ]
#     layout.controls = controls
#     layout.show(
#         centered=True,
#         warp_pointer=True,
#     )

layout = PopupRelativeLayout(
    qtile,
    width=1000,
    height=400,
    opacity=0.9,
    background=colors["darkblue"],
    initial_focus=None,
    close_on_click=False,
    controls=[
        PopupText(
            font=settings["text_font"],
            pos_x=1 / 20,
            pos_y=1 / 8,
            width=0.9,
            height=1 / 4,
            foreground="000000",
            fontsize=28,
            text="",
            h_align="center",
            v_align="middle",
            wrap=True,
            name="question"
        ),
        PopupText(
            font=settings["text_font"],
            pos_x=1 / 3 - 0.1,
            pos_y=2 / 3,
            width=0.1,
            height=0.1,
            fontsize=28,
            foreground="000000",
            text="Yes",
            h_align="center",
            v_align="middle",
            wrap=True,
            can_focus=True,
        ),
        PopupText(
            font=settings["text_font"],
            pos_x=2 / 3,
            pos_y=2 / 3,
            width=0.1,
            height=0.1,
            fontsize=28,
            foreground="000000",
            text="No",
            h_align="center",
            v_align="middle",
            wrap=True,
            can_focus=True,
        ),
    ],
)


@lazy.window.function
def close_app_with_warning_window(window):
    def double_kill():
        window.kill()
        layout.hide()

    layout._configure(qtile)
    # layout.controls[0].text = f"You sure you want to kill window\n{window.name}?"
    layout.update_controls(question=f"You sure you want to kill window\n{window.name}?")
    layout.controls[1].mouse_callbacks = {"Button1": double_kill}
    layout.controls[2].mouse_callbacks = {"Button1": layout.hide}
    layout.show(
        centered=True,
        warp_pointer=True,
    )
    logger.info(layout.controls)
