import turtle
import random
import json

class LSystem:
    
    DEFAULT_ACTIONS = {
        'A': 'draw', 'B': 'draw', 'C': 'draw', 
        'D': 'draw', 'E': 'draw', 'F': 'draw',
        'G': 'move', 'H': 'move', 'I': 'move',
        'J': 'move', 'K': 'move', 'L': 'move',
        '+': 'left',
        '-': 'right',
        '[': 'push',
        ']': 'pop'
    }

    def __init__(self, angle=0, actions={}, rules={}, axiom='', 
                 rand_unit=0, rand_angle=0, draw={}, trace=False, **kwargs):
        self.angle = angle
        self.actions = actions if actions else LSystem.DEFAULT_ACTIONS
        self.rules = rules
        self.axiom = axiom
        self.rand_unit = rand_unit
        self.rand_angle = rand_angle
        self.start_point = draw.get('start_point', [0, 0])
        self.start_heading = draw.get('start_heading', 0)
        self.default_order = draw.get('default_order', 5)
        self.default_unit = draw.get('default_unit', 5)
        self.fill_order = draw.get('fill_order', 0)
        self.fill_colors = draw.get('fill_colors', {})
        self.corner_radius = draw.get('corner_radius', 0)
        self.seq_colors = draw.get('seq_colors', [])
        self.seq_color_order = draw.get('seq_color_order', 0)
        self.trace = trace
        self.stack = []
        self.turnstack = 0
        self.max_x, self.max_y = (0, 0)
        self.color_index = -1

    def initpen(self):
        self.pen = turtle.Turtle(visible=False)
        self.pen.speed(0)
        self.pen.penup()
        w, h = turtle.screensize()
        self.pen.setpos(w * self.start_point[0], h * self.start_point[1])
        self.pen.setheading(self.start_heading)
        self.pen.pendown()

    @staticmethod
    def from_dict(dict, trace=False):
        return LSystem(**dict, trace=trace)

    @staticmethod
    def from_json(json_filename, trace=False):
        with open(json_filename) as json_file:
            json_dict = json.load(json_file)
        turtle.title(json_filename)
        return LSystem.from_dict(json_dict, trace)

    def get_angle(self):
        return ((random.random() * 2 - 1) * self.rand_angle + 1) * self.angle
        
    def get_unit(self, unit):
        return ((random.random() * 2 - 1) * self.rand_unit + 1) * unit
        
    def draw(self, unit):
        self.turn()
        u = self.get_unit(unit) - 2 * self.corner_radius
        self.pen.forward(u)
        x, y = self.pen.position()
        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)
        
    def move(self, unit):
        self.turn()
        self.pen.penup()
        self.draw(unit)
        self.pen.pendown()

    def left(self, unit):
        self.turnstack += self.get_angle()

    def right(self, unit):
        self.turnstack -= self.get_angle()

    def turn(self):
        if self.corner_radius:
            sig = -1 if self.turnstack < 0 else 1
            self.pen.circle(sig * self.corner_radius, abs(self.turnstack), int(self.corner_radius))
        else:
            self.pen.left(self.turnstack)
        self.turnstack = 0

    def push(self, unit):
        self.stack.append((self.pen.pos(), self.pen.heading(), self.turnstack))

    def pop(self, unit):
        pos, head, turnstack = self.stack.pop()
        self.pen.penup()
        self.pen.setpos(pos)
        self.pen.setheading(head)
        self.pen.pendown()
        self.pen.ht()
        self.turnstack = turnstack

    def noop(self, unit):
        pass
        
    def call_action(self, action, unit):
        if action == 'noop':
            return
        if self.trace:
            print(f'action: {action} unit: {unit}')
        map = {
            'draw': self.draw,
            'move': self.move,
            'left': self.left,
            'right': self.right,
            'push': self.push,
            'pop': self.pop
        }
        if action in map:
            map[action](unit)
        else:
            raise ValueError(f'Unknown action: {action}')

    def execute(self, string, order, unit):
        for var in string:
            if order <= 0 or var not in self.rules.keys():
                action = self.actions.get(var, 'noop')
                if self.trace and action != 'noop':
                    print(f'order #{order}: {var} -> [{action}]')
                self.call_action(action, unit)
            else:
                if self.seq_color_order and self.seq_colors and order == self.seq_color_order:
                    self.color_index = (self.color_index + 1) % len(self.seq_colors)
                    self.pen.color(self.seq_colors[self.color_index])
                if self.trace:
                    print(f'order #{order}: {var} -> {self.rules[var]}')
                if order == self.fill_order:
                    if var in self.fill_colors:
                        self.pen.color(self.fill_colors[var])
                    self.pen.begin_fill()
                for subst in self.rules[var]:
                    self.execute(subst, order-1, unit)
                if order == self.fill_order:
                    self.pen.end_fill()

    def demo(self, order=None, unit=None, **kwargs):
        if not order: 
            order = self.default_order
        if not unit:
            unit = self.default_unit
        turtle.mode('logo')
        turtle.clearscreen()
        turtle.tracer(False)
        self.initpen()
        self.execute(self.axiom, order, unit)
        turtle.update()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='L-System executor')
    parser.add_argument('input_file', type=str, help='The json definition of the L-System')
    parser.add_argument('-u', '--unit', type=float, help='The base unit of the drawing in pixels')
    parser.add_argument('-o', '--order', type=int, help='The depth of the recursion')
    parser.add_argument('-t', '--trace', action='store_true', help='Print tracing info to stdout')
    args = vars(parser.parse_args())
    LSystem.from_json(args['input_file'], trace=args['trace']).demo(**args)
    turtle.exitonclick()
