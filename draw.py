from math import sqrt, floor, pi, cos, sin, acos, asin

import geom2d
from geom2d import Point, Circle, Color

from geom2dimpl.svg import SVGPlane
from geom2dimpl.raster import RasterPlane
from geom2dimpl.image import ImageRaster
from geom2dimpl.tkinter import TkinterCanvasPlane

import Tkinter

PLANE_WIDTH = 12
PLANE_HEIGHT = 9
FLOWER_RADIUS = 3.0

IMAGE_WIDTH = 400
IMAGE_HEIGHT = 300

FP_THRESHOLD = 0.001
DIV_THRESHOLD = 1000
PRECISION_DIGITS = 5
NEAR = 0.2




def is_near_identical(point, points, near):
    if point in points:
        return True

    for other in points:
        if other.distance_to(point) < near:
            return True

    return False

def perform_intersections(circles, center, radius, near=NEAR):
    if len(circles) == 0:
        return

    circle_radius = circles[0].radius
    points = set(map(lambda c: c.center, circles))
    index = 1

    while index < len(circles):
        sel_circle = circles[index]
        for i in range(index):
            other_circle = circles[i]
            inter = sel_circle.intersection(other_circle)
            for p in inter:
                pr = Point(round(p.x, PRECISION_DIGITS),
                           round(p.y, PRECISION_DIGITS))
                if not is_near_identical(pr, points, near) \
                   and pr.distance_to(center) <= radius:
                    circle = Circle(pr, circle_radius)
                    circles.append(circle)
                    points.add(pr)
        index += 1

def create_flower_of_life():
    full_circles = overlapping_circles(3)
    all_circles = overlapping_circles(5)
    surr_circles = list(set(all_circles).difference(set(full_circles)))
    return (full_circles, surr_circles)

def is_arc_outside_circle(center, radius, start, end, circle):
    delta = end - start
    if end < start:
        delta += 1.0

    def is_outside(r, d):
        if abs(d) < float(radius) / DIV_THRESHOLD:
            return False
        point = Point(center.x + radius*cos(r * 2*pi),
                      center.y - radius*sin(r * 2*pi))
        if circle.center.distance_to(point) > circle.radius + FP_THRESHOLD:
            return True
        c = r + (d / 2)
        if c + (d / 4) > start + delta:
            return False
        return is_outside(c - (d / 4), d / 2) or is_outside(c + (d / 4), d / 2)
    return is_outside(start, delta)
        

def draw_circle_filtered(plane, circle, enclosing_circle, color):
    inter = enclosing_circle.intersection(circle)
    if len(inter) != 2:
        return
    else:
        rangles = []
        for p in inter:
            # Work out the angle from where the intersection point
            # is on the circle
            rad = acos((p.x - circle.center.x) / circle.radius)

            # Convert this angle in radians to a normalized angle in
            # the interval [0, 1]
            rangle = 0
            if p.y > circle.center.y:
                rangle = 0.5 + ((pi - rad) / (2*pi))
            else:
                rangle = rad / (2*pi)
            rangles.append(rangle)
        if is_arc_outside_circle(circle.center, circle.radius,
                                 rangles[0], rangles[1], enclosing_circle):
            rangles.reverse()
        extent = rangles[1] - rangles[0]
        if extent < 0:
            extent += 1.0
        plane.draw_circle_arc(circle, rangles[0], extent, color)


def draw_flower_of_life(plane, flower_pattern, center, radius, color):
    full_circles, surr_circles = flower_pattern

    circle_radius = radius / 3.0

    outer_circle = Circle(center, radius)
    plane.draw_circle(outer_circle, color)

    def transform(circle):
        circle_center = Point(circle.center.x*circle_radius + center.x,
                              circle.center.y*circle_radius + center.y)
        return Circle(circle_center, circle_radius)

    full_circles = map(transform, full_circles)
    surr_circles = map(transform, surr_circles)

    for circle in full_circles:
        plane.draw_circle(circle, color)

    for circle in surr_circles:
        for full_circle in full_circles:
            draw_circle_filtered(plane, circle, full_circle, color)


def overlapping_circles(n):
    if n < 0:
        return (n, [])

    if n == 0 or n == 1:
        return (n, [Circle(Point(0, 0), 1.0)])

    init_circles = []
    center = Point(0, 0)
    radius = 1.0
    circle1 = Circle(Point(center.x, center.y), radius)
    init_circles.append(circle1)

    circle2 = Circle(Point(center.x, center.y - radius), radius)
    init_circles.append(circle2)

    circles = list(init_circles)
    perform_intersections(circles, center, (n - 1) + FP_THRESHOLD)
    return circles

def draw_overlapping_circles(plane, center, radius, color, n, ocircles=None):
    if ocircles is None:
        ocircles = overlapping_circles(n)

    circle_radius = radius
    if n > 1:
        circle_radius = radius / (n - 1)
    for circle in ocircles:
        circle_center = Point(circle.center.x*circle_radius + center.x,
                              circle.center.y*circle_radius + center.y)
        dcircle = Circle(circle_center, circle_radius)
        plane.draw_circle(dcircle, color)


top = Tkinter.Tk()

flower_pattern = create_flower_of_life()

planes = []

canvas = Tkinter.Canvas(top, bg="white", height=600, width=800)
tk_plane = TkinterCanvasPlane(PLANE_WIDTH, PLANE_HEIGHT, canvas)
planes.append(tk_plane)

image_raster = ImageRaster(IMAGE_WIDTH, IMAGE_HEIGHT, geom2d.WHITE)
image_plane = RasterPlane(PLANE_WIDTH, PLANE_HEIGHT, image_raster)
planes.append(image_plane)

svg_plane = SVGPlane(PLANE_WIDTH, PLANE_HEIGHT, 'floweroflife.svg')
planes.append(svg_plane)

for plane in planes:
    draw_flower_of_life(plane, flower_pattern,
                        Point(PLANE_WIDTH / 2.0, PLANE_HEIGHT / 2.0),
                        FLOWER_RADIUS, geom2d.BLACK)

canvas.pack()
image_raster.save('floweroflife.png')
svg_plane.save()

top.mainloop()
