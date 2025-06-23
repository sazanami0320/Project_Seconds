from typing import Callable
class EffectManager:
    def __init__(self, writeln: Callable[[str], None]):
        self.zoom_flag = False
        self.move_flag = False
        self.writeln = writeln

    def zoomin(self, percentage: int):
        self.writeln(f"@action time=\"1000\" zoom=\"{percentage}\" layer=\"stage\" module=\"LayerNormalZoomModule\"")

    def move(self, x: int, y: int):
        self.writeln(f"@action time=\"1000\" x=\"{x}\" y=\"{y}\" layer=\"stage\" module=\"LayerNormalMoveModule\"")

    def bounce(self, vibration: int, layer: int, cycle: int):
        self.writeln(f"@action vibration=\"{vibration}\" layer=\"{layer}\" module=\"LayerJumpActionModule\" cycle=\"{cycle}\"")
    
    def parse_effect(self, effect_name: str):
        wa_flag = True # gerogero
        if effect_name == '放大背景':
            self.zoomin(150)
            self.zoom_flag = True
        elif effect_name == '放大并横向':
            self.zoomin(150)
            self.writeln(f";[TODO] 检查这一镜头的坐标")
            self.move(200, 0)
            self.zoom_flag = True
            self.move_flag = True
        elif effect_name == '放大并纵向':
            self.zoomin(150)
            self.writeln(f";[TODO] 检查这一镜头的坐标")
            self.move(0, 100)
            self.zoom_flag = True
            self.move_flag = True
        elif effect_name == '立绘跳动':
            self.bounce(20, 0, 700)
        else:
            self.writeln(f";[需求]重置效果")
            wa_flag = False
        if wa_flag:
            # FIXME
            self.writeln('@wact layer="stage"')

    def reset_effect(self):
        wa_flag = False
        if self.move_flag:
            self.move(0, 0)
            self.move_flag = False
            wa_flag = True
        if self.zoom_flag:
            self.zoomin(100)
            self.zoom_flag = False
            wa_flag = True
        if wa_flag:
            # FIXME
            self.writeln('@wact layer="stage"')
        


