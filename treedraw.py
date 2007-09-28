# Copyright (C) 2007 Alex Drummond <a.d.drummond@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301, USA.

"""
This module contains code for rendering labelled bracketings + movements
as images.
"""

import cairo
import md5

# Horizontal and vertical spacing between subtrees as a multiple of the
# font size used.
V_SPACING_FACTOR = 0.75
H_SPACING_FACTOR = 0.75

LABEL_V_SPACING_FACTOR = 0.2
LABEL_H_SPACING_FACTOR = 0.2

ARROW_SPACING_FACTOR = 0.2

BAR_CHAR = unichr(8242)

class TextExtents(object):
    """PyCairo returns a tuple for cairo_text_extents_t, which is a bit awkward
       to work with. This class wraps the tuple as a structure with
       named fields.
    """
    def __init__(self, tuple):
        self.x_bearing, self.y_bearing, self.width, \
        self.height, self.x_advance, self.y_advance = tuple

class CairoState(object):
    def __init__(self, surface, font_size, line_width=2.0):
        self.context = cairo.Context(surface)
        self.context.set_font_size(font_size)
        self.context.set_line_width(line_width)
        self.font_size = font_size

class Label(object):
    """The label of a node in a syntax tree."""

    def __init__(self, text, bar_level):
        self.text = text
        self.bar_level = bar_level

    def size(self, cs):
        """Calculate the width and height (in pixels) for the label
           given a CairoState object."""
        extents = TextExtents(cs.context.text_extents(self.text + BAR_CHAR * self.bar_level))
        tdims = (extents.width, extents.height)
        tdims_no_bar = None
        if self.bar_level == 0:
            tdims_no_bar = tdims
        else:
            extents_no_bar = TextExtents(cs.context.text_extents(self.text))
            tdims_no_bar = (extents_no_bar.width, extents_no_bar.height)
        self.dimensions = (
            tdims[0] + int(cs.font_size * LABEL_H_SPACING_FACTOR),
            tdims[1] + int(cs.font_size * LABEL_V_SPACING_FACTOR)
        )
        self.dimensions_no_bar = (
            tdims_no_bar[0] + int(cs.font_size * LABEL_H_SPACING_FACTOR),
            tdims_no_bar[1] + int(cs.font_size * LABEL_V_SPACING_FACTOR)
        )

    def __repr__(self):
        return self.text + "'" * self.bar_level

class TreeNode(object):
    """A node in a syntax tree."""

    def __init__(self, label, children):
        self.label = label
        self.children = children

    def size(self, cs, root=False):
        self.label.size(cs)
        label_dims = self.label.dimensions
        tallest_child_height = 0
        total_width = 0
        i = 0
        for i in xrange(len(self.children)):
            self.children[i].size(cs)
            total_width += self.children[i].dimensions[0]
            if i > 0:
                total_width += H_SPACING_FACTOR * cs.font_size
            if self.children[i].dimensions[1] > tallest_child_height:
                tallest_child_height = self.children[i].dimensions[1]
        self.dimensions = (total_width,
                           label_dims[1] + \
                           tallest_child_height + \
                           (V_SPACING_FACTOR * cs.font_size))
        if label_dims[0] > total_width:
            self.dimensions = (label_dims[0], self.dimensions[1])

        # If this is a root node, add some extra space at the bottom for
        # arrows.
        if root:
            self.dimensions = (self.dimensions[0],
                               self.dimensions[1] + \
                               (cs.font_size * ARROW_SPACING_FACTOR))

    def hash(self):
        """This converts a sized tree into a string and hashes the string to give a
           unique hash for the tree.
        """
        assert hasattr(self, "dimensions")
        strings = [ ]
        def traverse(node):
            print "HERE"
            strings.append(node.label.text + node.label.bar_level * "'")
            for c in node.children:
                strings.append('[')
                traverse(c)
                strings.append(']')
        traverse(self)
        hash_string = ''.join(strings)
        return md5.md5(hash_string).hexdigest()

    def __repr__(self):
        return "[" + str(self.label) + ' '.join(map(str, self.children)) + ']'

def width_of_children(children, cs):
    total = 0
    for i in xrange(len(children)):
        total += children[i].dimensions[0]
        if i < len(children) - 1:
            total += H_SPACING_FACTOR * cs.font_size
    return total

def node_at_path(node, path):
    for i in path:
        node = node.children[i]
    return node
def parent_of_node_at_path(node, path): return node_at_path(node, path[0:-1])

def draw_tree_(tree_node, start_x, start_y, movements, cs, current_path, node_to_coord):
    """Does the heavy lifting for draw_tree."""
    #root_x = start_x + tree_node.dimensions[0] - int(tree_node.label.dimensions[0] / 2)
    #root_y = start_y + tree_node.dimensions[1]

    # Draw the label.
    cs.context.move_to(start_x - int(tree_node.label.dimensions[0] / 2), start_y)
    cs.context.show_text(tree_node.label.text + BAR_CHAR * tree_node.label.bar_level)
    cs.context.stroke()

    # Draw the children.
    # First, calculate the offset from the center of the first child.
    current_offset = None
    if len(tree_node.children):
        current_offset = int((tree_node.children[0].dimensions[0] - tree_node.dimensions[0]) / 2)
    child_y = start_y + tree_node.label.dimensions[1] + V_SPACING_FACTOR * cs.font_size
    for i in xrange(len(tree_node.children)):
        # Draw the child.
        child_x = start_x + current_offset
        draw_tree_(tree_node.children[i], child_x, child_y, [], cs, current_path + [i], node_to_coord)
        # Store the coordinates of the child (we use these to draw movement
        # arrows). We don't want bars to influence the middle position of
        # labels so correct for this.
        node_to_coord.append(
            (
            current_path + [i],
            (child_x - \
             ((tree_node.children[i].label.dimensions[0] - \
               tree_node.children[i].label.dimensions_no_bar[0]) / 2),
             child_y)
            ))
        # Draw a line from this node to the child.
        x1 = start_x
        y1 = start_y + 2 # Small amount of spacing.
        x2 = child_x
        # Avoid just-off-vertical lines
        if abs(x2 - x1) <= 3:
            x2 = x1
        # We want to draw the line to the middle of the label EXCLUDING bars,
        # so if the label has bars, correct the x2 value.
        if tree_node.children[i].label.bar_level != 0:
            x2 -= int((tree_node.children[i].label.dimensions[0] - tree_node.children[i].label.dimensions_no_bar[0]) / 2)
        y2 = child_y - tree_node.children[i].label.dimensions[1]
        cs.context.move_to(x1, y1)
        cs.context.line_to(x2, y2)
        # Update offset.
        if i < len(tree_node.children) - 1:
            current_offset += tree_node.children[i].dimensions[0] + int(tree_node.children[i + 1].dimensions[0] / 2)
            current_offset += H_SPACING_FACTOR * cs.font_size

    cs.context.stroke()

    return node_to_coord

def draw_tree(tree_node, movements, cs):
    """Draws a tree given a root node given a CairoState object."""
    tree_node.size(cs, root=True)

    node_to_coord = draw_tree_(tree_node, int(tree_node.dimensions[0] / 2) + 1, tree_node.label.dimensions[1], movements, cs, [], [])

    # Work out the max height of a line of text (a tad unscientific).
    MAX_TEXT_HEIGHT = TextExtents(cs.context.text_extents("Ag" + BAR_CHAR)).height

    # Draw any movements that were specified.
    def coords_for_path(path):
        for p, c in node_to_coord:
            if p == path:
                return c, node_at_path(tree_node, path)
        assert False
    for m in movements:
        cs.context.set_dash([int(cs.font_size * 0.15), int(cs.font_size * 0.1), int(cs.font_size * 0.075)])

        coords_from, node_from = coords_for_path(m[0])
        coords_to, node_to = coords_for_path(m[1])
        shift_from = (len(node_from.children) == 0 and (0,) or (node_from.dimensions[1],))[0]
        shift_to = (len(node_to.children) == 0 and (0,) or (node_to.dimensions[1],))[0]

        # HORRIBLE TEMPORARY HACK.
        # At some point we'll have to move to a more sophisticated algorithm
        # for drawing arrows in the right places, since this one doesn't
        # guarantee that the arrow won't be drawn across part of the tree.
        extra_down = 0
        parent = parent_of_node_at_path(tree_node, m[0])
        for n in parent.children:
            if n is not parent and n.dimensions[1] > shift_from:
                extra_down = n.dimensions[1] + MAX_TEXT_HEIGHT + int(cs.font_size * ARROW_SPACING_FACTOR)

        arrow_start = (coords_from[0], coords_from[1] + shift_from + cs.font_size * ARROW_SPACING_FACTOR)
        arrow_step1 = None
        arrow_step2 = None
        arrow_step3 = None
        if coords_to[1] + node_to.dimensions[1] > coords_from[1] + node_from.dimensions[1]:
            # If we're moving down or sideways.
            arrow_step1 = (arrow_start[0], coords_to[1] + shift_to + int(cs.font_size * ARROW_SPACING_FACTOR * 2))
            arrow_step2 = (coords_to[0] + int(node_to.dimensions[0] / 2), arrow_step1[1])
            arrow_step3 = (arrow_step2[0], arrow_step2[1] - int(cs.font_size * ARROW_SPACING_FACTOR))
        else:
            # If we're moving up.
            arrow_step1 = (arrow_start[0], arrow_start[1] + int(cs.font_size * ARROW_SPACING_FACTOR) + extra_down)
            arrow_step2 = (coords_to[0], arrow_step1[1])
            arrow_step3 = (arrow_step2[0], coords_to[1] + shift_to + cs.font_size * ARROW_SPACING_FACTOR + MAX_TEXT_HEIGHT)
        cs.context.move_to(arrow_start[0], arrow_start[1])
        cs.context.line_to(arrow_step1[0], arrow_step1[1])
        cs.context.line_to(arrow_step2[0], arrow_step2[1])
        cs.context.line_to(arrow_step3[0], arrow_step3[1])
        cs.context.stroke()
        # Draw the arrowhead.
        cs.context.set_dash([])
        cs.context.move_to(arrow_step3[0], arrow_step3[1])
        cs.context.line_to(arrow_step3[0] - int(cs.font_size * 0.8 * ARROW_SPACING_FACTOR), arrow_step3[1] + int(cs.font_size * 0.8 * ARROW_SPACING_FACTOR))
        cs.context.move_to(arrow_step3[0], arrow_step3[1])
        cs.context.line_to(arrow_step3[0] + int(cs.font_size * 0.8 * ARROW_SPACING_FACTOR), arrow_step3[1] + int(cs.font_size * 0.8 * ARROW_SPACING_FACTOR))
        cs.context.stroke()


#
# TEST CODE.
#
#surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 300)
#context = cairo.Context(surface)
#cs = CairoState(surface, 20)
#root = TreeNode(Label("S", 0), [TreeNode(Label("NP", 3), []), TreeNode(Label("VP", 0), [TreeNode(Label("BP", 0), [])]), TreeNode(Label("QP", 0), [])])
#root.size(cs)
#print root.md5_hash()
#root = TreeNode(cs, Label(cs, "S", 0), [TreeNode(cs, Label(cs, "NP", 3), [TreeNode(cs, Label(cs, "NP", 3), [])]), TreeNode(cs, Label(cs, "VP", 0), [TreeNode(cs, Label(cs, "BP", 0), [])]), TreeNode(cs, Label(cs, "QP", 3), [])])
#root = TreeNode(cs, Label(cs, "S", 0), [TreeNode(cs, Label(cs, "NP", 3), []), TreeNode(cs, Label(cs, "VP", 0), [TreeNode(cs, Label(cs, "BP", 0), [])]), TreeNode(cs, Label(cs, "QP", 3), []), TreeNode(cs, Label(cs, "ZP", 3), [])])
#root = TreeNode(cs, Label(cs, "S", 0), [TreeNode(cs, Label(cs, "C", 0), [])])
#root = TreeNode(cs, Label(cs, "S", 0), [TreeNode(cs, Label(cs, "C", 0), []), TreeNode(cs, Label(om, "D", 0), [])])
#print root
#draw_tree(root, [((1,), (0,))], cs)
#draw_tree(root, [], cs)
#draw_tree(root, [], om)
#surface.write_to_png("test.png")

