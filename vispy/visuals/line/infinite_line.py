import numpy as np

from ... import gloo
from ..visual import Visual


# Horizontal infinite line
VERT_SHADER_H = """
    attribute vec2 a_pos;
    varying vec4 v_color;

    void main() {
        vec4 pos = vec4(a_pos, 0, 1);
        pos.x = $render_to_visual(pos).x;
        gl_Position = $transform(pos);
        gl_PointSize = 10;
        v_color = $color;

    }
    """

# Vertical infinite line
VERT_SHADER = """
    attribute vec2 a_pos;
    varying vec4 v_color;

    void main() {
        vec4 pos = vec4(a_pos, 0, 1);

        if($is_vertical==1)
        {
            pos.y = $render_to_visual(pos).y;
        }
        else
        {
            pos.x = $render_to_visual(pos).x;
        }

        gl_Position = $transform(pos);
        gl_PointSize = 10;
        v_color = $color;
    }
    """

FRAG_SHADER = """
    varying vec4 v_color;

    void main() {
        gl_FragColor = v_color;
    }
    """


class InfiniteLineVisual(Visual):
    """Infinite horizontal or vertical line for 2D plots.

    Parameters
    ----------
    pos : float
        Position of the line along the axis.
    color : list, tuple, or array
        The color to use when drawing the line. If an array is given, it
        must be of shape (1, 4) and provide one rgba color per vertex.
    vertical:
        True for drawing a vertical line, False for an horizontal line
    """

    def __init__(self, pos=None, color=(1.0, 1.0, 1.0, 1.0), vertical=True):
        """

        """
        Visual.__init__(self, vcode=VERT_SHADER, fcode=FRAG_SHADER)

        self._changed = {'pos': False, 'color': False}

        self.pos_buf = gloo.VertexBuffer()
        # The Visual superclass contains a MultiProgram, which is an object
        # that behaves like a normal shader program (you can assign shader
        # code, upload values, set template variables, etc.) but internally
        # manages multiple ModularProgram instances, one per view.

        # The MultiProgram is accessed via the `shared_program` property, so
        # the following modifications to the program will be applied to all
        # views:
        self.shared_program['a_pos'] = self.pos_buf
        self._program.vert['is_vertical'] = 1 if vertical else 0

        self._need_upload = False
        self._is_vertical = bool(vertical)
        self._pos = np.zeros((2, 2), dtype=np.float32)

        # Visual keeps track of draw mode, index buffer, and GL state. These
        # are shared between all views.
        self._draw_mode = 'line_strip'
        self.set_gl_state('translucent', depth_test=False)

        self.set_data(pos=pos, color=color)

    def set_data(self, pos=None, color=None):
        if pos is not None:
            pos = float(pos)
            xy = self._pos
            if self._is_vertical:
                xy[0, 0] = pos
                xy[0, 1] = -1
                xy[1, 0] = pos
                xy[1, 1] = 1
            else:
                xy[0, 0] = -1
                xy[0, 1] = pos
                xy[1, 0] = 1
                xy[1, 1] = pos
            self._changed['pos'] = True

        if color is not None:
            if type(color) not in [tuple, list, np.ndarray] and len(color) != 4:
                raise ValueError('color must be a float rgba tuple, list or array')
            self._color = np.ascontiguousarray(list(color), dtype=np.float32)
            self._changed['color'] = True

    @property
    def color(self):
        return self._color

    @property
    def pos(self):
        if self._is_vertical:
            return self._pos[0, 0]
        else:
            return self._pos[0, 1]

    @property
    def is_vertical(self):
        return self._is_vertical

    def _prepare_transforms(self, view=None):
        program = view.view_program
        transforms = view.transforms
        program.vert['render_to_visual'] = transforms.get_transform('render', 'visual')
        program.vert['transform'] = transforms.get_transform('visual', 'render')

    def _prepare_draw(self, view=None):
        """This method is called immediately before each draw.

        The *view* argument indicates which view is about to be drawn.
        """

        if self._changed['pos']:
            self.pos_buf.set_data(self._pos)
            self._changed['pos'] = False

        if self._changed['color']:
            self._program.vert['color'] = self._color
            self._changed['color'] = False
