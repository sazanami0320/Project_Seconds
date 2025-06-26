from typing import Callable, Optional
from .stage import Stage
class EffectManager:
    def __init__(self, writeln: Callable[[str], None], stage: Stage):
        self.zoom_flag = False
        self.move_flag = False
        self.writeln = writeln
        self.stage = stage

    def zoomin(self, percentage: int, back_hook: Optional[Callable]=None):
        self.writeln('@backlay')
        if back_hook is not None:
            back_hook()
        self.writeln('@trans layer="base" time="500" method="crossfade"')
        self.writeln(f"@action time=\"0\" zoom=\"{percentage}\" layer=\"stage\" page=\"back\" module=\"LayerNormalZoomModule\"")
        self.writeln('@wt')
        self.writeln('@wact layer="stage"')

    def move(self, x: int, y: int, time: int):
        self.writeln(f"@action time=\"{time}\" x=\"{x}\" y=\"{y}\" layer=\"stage\" module=\"LayerNormalMoveModule\"")

    def loopxmove(self, start: int, end: int, time: int):
        self.writeln(f"@action start=\"{start}\" end=\"{end}\" time=\"{time}\" layer=\"stage\" module=\"LayerLoopMoveXModule\"")

    def loopymove(self, start: int, end: int, time: int):
        self.writeln(f"@action start=\"{start}\" end=\"{end}\" time=\"{time}\" layer=\"stage\" module=\"LayerLoopMoveYModule\"")

    def bounce(self, vibration: int, layer: int, cycle: int):
        self.writeln(f"@action vibration=\"{vibration}\" layer=\"{layer}\" module=\"LayerJumpActionModule\" cycle=\"{cycle}\"")
    
    def parse_effect(self, effect_name: str):
        if effect_name == '放大背景':
            self.zoomin(200, self.stage.clear_fg)
            self.zoom_flag = True
        elif effect_name == '放大并横向':
            self.zoomin(200)
            self.writeln(f";[TODO] 检查这一镜头的坐标")
            self.loopxmove(0, 700, 16000)
            self.zoom_flag = True
            self.move_flag = True
        elif effect_name == '放大并纵向':
            self.zoomin(200)
            self.writeln(f";[TODO] 检查这一镜头的坐标")
            self.loopymove(0, 500, 16000)
            self.zoom_flag = True
            self.move_flag = True
        elif effect_name == '立绘跳动':
            self.bounce(20, 0, 700)
        else:
            self.writeln(f";[需求]重置效果")

    def reset_effect(self):
        if self.move_flag:
            self.move_flag = False
            self.writeln('@stopaction layer="stage"')
        if self.zoom_flag:
            self.zoomin(100, self.stage.render_on_back)
            self.zoom_flag = False
        


