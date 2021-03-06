import turtle
import random
import json

class LSystem:
    ''' L-system renderer.
    
    An L-system or Lindenmayer system is a parallel rewriting system and a type 
    of formal grammar. An L-system consists of an alphabet of symbols that can 
    be used to make strings, a collection of production rules that expand each 
    symbol into some larger string of symbols, an initial "axiom" string from 
    which to begin construction, and a mechanism for translating the generated 
    strings into geometric structures. [Source](https://en.wikipedia.org/wiki/L-system)
    
    Each symbol corresponds to a character and can be optionally associated 
    with a drawing action performed by a [turtle graphics engine](https://en.wikipedia.org/wiki/Turtle_graphics).
    The following actions are implemented:
    
      - `draw`: draw forward `unit` pixels
      - `move`: move forward `unit` pixels
      - `left`: turn left `angle` degrees
      - `right`: turn right `angle` degrees
      - `push`: save current position and heading
      - `pop`: restore last saved position and heading
      
    The default association between symbols and actions follows the 
    [Inkspace](https://inkscape.org) L-System renderer alphabet and can be found 
    in LSystem.DEFAULT_ACTIONS. In nutshell:

      - `A`, `B`, `C`, `D`, `E`, `F`: draw forward
      - `G`, `H`, `I`, `J`, `K`, `L`: move forward
      - `+`: turn left
      - `-`: turn right
      - `[`: save position
      - `]`: restore position
      - other symbols do not cause any drawing action.
    '''
    
    DEFAULT_ACTIONS = {
        'A': 'draw_forward', 'B': 'draw_forward', 'C': 'draw_forward', 
        'D': 'draw_forward', 'E': 'draw_forward', 'F': 'draw_forward',
        'G': 'move_forward', 'H': 'move_forward', 'I': 'move_forward',
        'J': 'move_forward', 'K': 'move_forward', 'L': 'move_forward',
        '+': 'left_turn',
        '-': 'right_turn',
        '[': 'save_state',
        ']': 'restore_state'
    }

    def __init__(self, rules={}, axiom='', angle=0, left_angle=None, right_angle=None, actions={}, 
                 rand_unit=0, rand_angle=0, draw={}, trace=False, **kwargs):
        ''' Creates a new L-System renderer.
        
        Params:
          - rules: The substitution rules map of the L-System.
          - axiom: The initial axiom string of the L-System
          - angle: The angle used for turning in degrees
          - left_angle: The angle used for turning left in degrees. Defaults to
                None in which case `angle` will be used.
          - right_angle: The angle used for turning right in degrees. Defaults to
                None in which case `angle` will be used.
          - actions: The symbol -> action map. If None, LSystem.DEFAULT_ACTIONS
                map will be used.
          - rand_unit: randomize the unit length at each iteration by this 
                percentage. Defaults to 0.
          - rand_angle: randomize the turn angle at each iteration by this 
                percentage. Defaults to 0.
          - draw: additional parameters for drawing the default curve.
          - trace: print debugging messages to stdout while rendering the 
                L-System.
              
        Draw map keys:
          - start_point: The starting point of the drawing. Tuple of floats
                in -1..1 scale. Defaults to [0, 0] (the center of the screen)
          - start_heading: The orientation of the drawing in degrees. 
                Defaults to 0 (up).
          - default_order: The default order of the system (number of 
                recursions). Defaults to 5.
          - default_unit: The default number of pixels to be drawn by forward
                draw action. Defaults to 5.
          - fill_order: Fill the drawing at this order. Defaults to zero (
                no filling).
          - fill_colors: symbol (str) -> color (str) map to be used when 
                filling the drawing. Color strings are defined by the turtle
                library.
          - corner_radius: If greater than zero, draw rounded corners with this
                radius. Defaults to zero.
          - seq_color_order: Change the color the line at this order level.
                Defaults to zero (no change of color).
          - seq_colors: List of color strings to cycle when changing the color
                of the line. Defaults to empty list (no change of color).
        '''
        self.left_angle = left_angle if left_angle is not None else angle
        self.right_angle = right_angle if right_angle is not None else angle
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
        self._initpen()

    def _initpen(self):
        self.pen = turtle.Turtle(visible=False)
        self.pen.speed(0)
        self.pen.penup()
        w, h = turtle.screensize()
        self.pen.setpos(w * self.start_point[0], h * self.start_point[1])
        self.pen.setheading(self.start_heading)
        self.pen.pendown()

    @staticmethod
    def from_json(json_filename, trace=False):
        ''' Initializes the L-System from a json file. 
        
        For the possible keys in the json file see the LSystem() constructor
        docstring.
        
        Params:
            - json_filename: The file name of the json file.
        '''
        with open(json_filename) as json_file:
            json_dict = json.load(json_file)
        turtle.title(json_filename)
        return LSystem(**json_dict, trace=trace)

    def _get_angle(self, base_angle):
        if self.rand_angle:
            return ((random.random() * 2 - 1) * self.rand_angle + 1) * base_angle
        else:
            return base_angle
        
    def _get_unit(self, unit):
        return ((random.random() * 2 - 1) * self.rand_unit + 1) * unit
        
    def draw(self, unit):
        ''' Implements the `draw` action. '''
        self._turn()
        u = self._get_unit(unit) - 2 * self.corner_radius
        self.pen.forward(u)
        x, y = self.pen.position()
        self.max_x = max(self.max_x, x)
        self.max_y = max(self.max_y, y)
        
    def move(self, unit):
        ''' Implements the `move` action. '''
        self._turn()
        self.pen.penup()
        self.draw(unit)
        self.pen.pendown()

    def left(self, unit):
        ''' Implements the `left` action. '''
        # turnstack simply aggregates all turns before a forward move.
        # This way we get better drawings with rounded corners.
        self.turnstack += self._get_angle(self.left_angle)

    def right(self, unit):
        ''' Implements the `right` action. '''
        self.turnstack -= self._get_angle(self.right_angle)

    def _turn(self):
        # Executes the accumulated turns in the turnstack.
        if self.corner_radius:
            sig = -1 if self.turnstack < 0 else 1
            self.pen.circle(sig * self.corner_radius, abs(self.turnstack), int(self.corner_radius))
        else:
            self.pen.left(self.turnstack)
        self.turnstack = 0

    def push(self, unit):
        ''' Implements the `push` action. '''
        self.stack.append((self.pen.pos(), self.pen.heading(), self.turnstack))

    def pop(self, unit):
        ''' Implements the `pop` action. '''
        pos, head, turnstack = self.stack.pop()
        self.pen.penup()
        self.pen.setpos(pos)
        self.pen.setheading(head)
        self.pen.pendown()
        self.pen.ht()
        self.turnstack = turnstack

    def call_action(self, action, unit):
        ''' Executes an action. 
        
        Params:
            - action: the name of the action as referred by the actions map.
            - unit: Number of pixels to be used in forward draw.
        '''
        if action == 'noop':
            return
        if self.trace:
            print(f'action: {action} unit: {unit}')
        map = {
            'draw_forward': self.draw,
            'move_forward': self.move,
            'left_turn': self.left,
            'right_turn': self.right,
            'save_state': self.push,
            'restore_state': self.pop
        }
        if action in map:
            map[action](unit)
        else:
            raise ValueError(f'Unknown action: {action}')

    def execute(self, string, order, unit):
        ''' Executes the actions derived from a given string.
        
        Params:
            - string: The L-System string to be executed.
            - order: The remaining order (number of recursions) to be unfolded.
            - unit: Number of pixels to be used in forward draw.
        '''
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
        ''' Draws the L-System with the predefined drawing arguments. 
        
        Params:
            - order: The order (number of recursions) to be unfolded.
            - unit: Number of pixels to be used in forward draw.
        '''
        if not order: 
            order = self.default_order
        if not unit:
            unit = self.default_unit
        turtle.mode('logo')
        turtle.clearscreen()
        turtle.tracer(False)
        self._initpen()
        self.execute(self.axiom, order, unit)
        turtle.update()

if __name__ == '__main__':
    import argparse
    exit_msg = 'Click on the drawing window to exit.'
    parser = argparse.ArgumentParser(description='L-System renderer', 
                                     epilog=exit_msg)
    parser.add_argument('input_file', type=str, help='json definition of the L-System')
    parser.add_argument('-u', '--unit', type=float, help='base unit of the drawing in pixels')
    parser.add_argument('-o', '--order', type=int, help='depth of the recursion')
    parser.add_argument('-t', '--trace', action='store_true', help='print tracing info to stdout')
    args = vars(parser.parse_args())
    LSystem.from_json(args['input_file'], trace=args['trace']).demo(**args)
    print(exit_msg)
    turtle.exitonclick()
