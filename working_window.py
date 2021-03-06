import sys
import gtk
import cairo
import random
import math
import glib
from soldier import Soldier
from usRifleman import USrifleman
from talibanRifleman import TalibanRifleman
from shotline import ShotLine
from cover import Cover
import csv

#Global Window Parameters
WIDTH = 1128
HEIGHT = 846
TIME_BETWEEN_FRAMES = 100 #in milliseconds

class SimArea(gtk.DrawingArea):

    def __init__(self, input_file):
        super(SimArea, self).__init__()

        #class variables
        self.inSim = False #whether or not the simulation is in progress
        self.input_file = input_file
        self.red_combatants = [] #list of all red soldier objects
        self.blue_combatants = [] #list of all blue soldiers objects
        self.mortars = []
        self.shots = [] #list of all active ShotLine objects
        self.mortar_shots = []
        self.cover_objects = []
        self.count = 0
        ######TEMP VARIABLES#####START
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.rLeft = False
        self.rRight = False
        ######TEMP VARIABLES#####END

        #sets the size of the drawing area
        self.set_size_request(WIDTH, HEIGHT)#TODO change according to new picture
        #event listener that determines how SimArea displays itself
        self.connect("expose-event", self.expose)
        self.init_sim()

    def on_timer(self):
        #called for each tick of the simulation
        self.count += 1
        if self.inSim:
            #check simulation processes
            # if self.count%10 == 0:
            #     self.observe()
            #     self.decide()
            #     self.act()
            self.move()#TODO TEMP?
            self.queue_draw() #gtk function to draw all queued actions
            return True
        else:
            return False

    def observe(self):
        #TODO implement random combatant selection
        for red in self.red_combatants:
            red.observe()
        for blue in self.blue_combatants:
            blue.observe()
        # for mortar in self.mortars:
        #     mortar.observe() #TODO IS THIS IMPLEMENTED

    def decide(self):
        #TODO implement random combatant selection
        for red in self.red_combatants:
            red.decide()
        for blue in self.blue_combatants:
            blue.decide()
        # for mortar in self.mortars:
        #     mortar.decide() #TODO IS THIS IMPLEMENTED

    def act(self):
        #TODO implement random combatant selection
        for red in self.red_combatants:
            isShot, target, shotSuccess = red.act()
            if isShot:
                self.shots.append(ShotLine(red.posx, red.posy, target.posx, target.posy, shotSuccess))
        for blue in self.blue_combatants:
            isShot, target, shotSuccess = blue.act()
            if isShot:
                self.shots.append(ShotLine(blue.posx, blue.posy, target.posx, target.posy, shotSuccess))
        # for mortar in self.mortars:
        #     mortar.act() #TODO IS THIS IMPLEMENTED

    def init_sim(self):
        #initializes the simulation by reading all data from a csv
        with open(self.input_file, 'rb') as f:
            reader = csv.reader(f)
            input_list = list(reader)
        self.inSim = True

        for i,line in enumerate(input_list):
            if line[0] == 'blue':
                self.blue_combatants.append(USrifleman("soldier"+str(i), line[0], int(line[1]), int(line[2]), int(line[3]), int(line[4]), int(line[5])))
            elif line[0] == 'red':
                self.red_combatants.append(TalibanRifleman("soldier"+str(i), line[0], int(line[1]), int(line[2]), int(line[3]), int(line[4]), int(line[5])))
            elif line[0] == 'cover':
                self.cover_objects.append(Cover(int(line[1]), int(line[2]), int(line[3]), int(line[4])))
            else:
                print "improper csv line: "
                print line

        glib.timeout_add(TIME_BETWEEN_FRAMES, self.on_timer) #Tick

    def expose(self, widget, event):
        #method to draw all objects
        cr = widget.window.cairo_create() #creates a cairo object (used for all drawing)

        if self.inSim:
            #sets the background of the window to be the satellite image of the battlefield
            pixbuf = gtk.gdk.pixbuf_new_from_file('GUI/bg.png')
            widget.window.draw_pixbuf(widget.style.bg_gc[gtk.STATE_NORMAL], pixbuf, 0, 0, 0,0)

            for red in self.red_combatants:
                self.draw_red_soldiers(cr, red)
            for blue in self.blue_combatants:
                self.draw_blue_soldiers(cr, blue)
            for mortar in self.mortars: #TODO cheack implementation with Wayne
                self.draw_mortars(cr, mortar)
            for shot in self.shots:
                cr.set_line_width(2)
                if shot.hit:
                    cr.set_source_rgba(0, 0, 0, shot.alpha) #shot is black if hit
                else:
                    cr.set_source_rgba(1, 1, 1, shot.alpha) #white if miss
                cr.move_to(shot.source_x, shot.source_y)
                cr.line_to(shot.target_x, shot.target_y)
                cr.stroke()
                shot.degrade() #increases the transparency for future ticks
            self.shots = [shot for shot in self.shots if shot.alpha > 0]
            for shot in self.mortar_shots:
                if shot.detonate:
                    cr.set_source_rgba(1,1,1,0.25)
                    cr.arc(shot.posx, shot.posy, 50, 0, 2*math.pi) #TODO change 5 to proper distance -- implement in mortarshot?
                    cr.fill()
                    #cr.set_source_rgba(0, 0, 0, 0.25)
                    cr.set_source_rgba(1,1,1,0.35)
                    cr.arc(shot.posx, shot.posy, 15, 0, 2*math.pi)
                    cr.fill()
                    cr.set_source_rgba(1,1,1,0.6)
                    cr.arc(shot.posx, shot.posy, 5, 0, 2*math.pi)
                    cr.fill()
                else:
                    cr.set_line_width(1)
                    cr.set_source_rgb(0,0,0)
                    cr.arc(shot.posx, shot.posy, 3, 0, 2*math.pi)
                    cr.stroke_preserve()
                    cr.set_source_rgb(1,1,1)
                    cr.fill()
                shot.update()
            self.mortar_shots = [shot for shot in self.mortar_shots if shot.detonation_time > 0]
            for cover in self.cover_objects:
                pass #TODO implement
        else:
            self.sim_over(cr)

    def sim_over(self, cr):
        #TODO currently an unused method, may use later though
        w = self.allocation.width / 2
        h = self.allocation.height / 2

        (x, y, width, height, dx, dy) = cr.text_extents("Simulation Over")

        cr.set_source_rgb(65535, 65535, 65535)
        cr.move_to(w - width/2, h)
        cr.show_text("Simulation Over")
        self.inSim = False

    def move(self): #TODO TEMP: implements temporary keyboard movement
        if self.left:
            for red in self.red_combatants:
                red.posx -= 1
            for blue in self.blue_combatants:
                blue.posx -= 1

        if self.right: 
            for red in self.red_combatants:
                red.posx += 1
            for blue in self.blue_combatants:
                blue.posx += 1

        if self.up:
            for red in self.red_combatants:
                red.posy -= 1
            for blue in self.blue_combatants:
                blue.posy -= 1

        if self.down:
            for red in self.red_combatants:
                red.posy += 1
            for blue in self.blue_combatants:
                blue.posy += 1

        if self.rRight:
            for red in self.red_combatants:
                red.orientation -= 0.1
            for blue in self.blue_combatants:
                blue.orientation += 0.1

        if self.rLeft:
            for red in self.red_combatants:
                red.orientation += 0.1
            for blue in self.blue_combatants:
                blue.orientation -= 0.1

    #####TEMP METHODS?######START
    def on_key_down(self, event):
        key = event.keyval
        if key == gtk.keysyms.a:
            self.left = True
        elif key == gtk.keysyms.d:
            self.right = True
        elif key == gtk.keysyms.w:
            self.up = True
        elif key == gtk.keysyms.s:
            self.down = True
        elif key == gtk.keysyms.q:
            self.rLeft = True
        elif key == gtk.keysyms.e:
            self.rRight = True
        elif key == gtk.keysyms._1:
            b = self.blue_combatants[0]
            r = self.red_combatants[0]
            shot = MortarShot(b.posx, b.posy, 450, 450)
            self.mortar_shots.append(shot)
        elif key == gtk.keysyms._2:
            b = self.blue_combatants[1]
            r = self.red_combatants[1]
            shot = ShotLine(b.posx, b.posy, r.posx, r.posy, False)
            self.shots.append(shot)
        elif key == gtk.keysyms._3:
            b = self.blue_combatants[0]
            r = self.red_combatants[0]
            shot = ShotLine(r.posx, r.posy, b.posx, b.posy, False)
            self.shots.append(shot)
        elif key == gtk.keysyms._4:
            b = self.blue_combatants[1]
            r = self.red_combatants[1]
            shot = ShotLine(r.posx, r.posy, b.posx, b.posy, True)
            self.shots.append(shot)

    def on_key_up(self, event):
        key = event.keyval
        if key == gtk.keysyms.a:
            self.left = False
        elif key == gtk.keysyms.d:
            self.right = False
        elif key == gtk.keysyms.w:
            self.up = False
        elif key == gtk.keysyms.s:
            self.down = False
        elif key == gtk.keysyms.q:
            self.rLeft = False
        elif key == gtk.keysyms.e:
            self.rRight = False
    #####TEMP METHODS?######END

    '''///////////DRAW METHODS///////////'''
    def draw_blue_soldiers(self, cr, blue):
        cr.set_line_width(1)
        cr.set_source_rgb(0, 0, 0)
        cr.arc(blue.posx, blue.posy, 5, 0, 2*math.pi)
        cr.stroke_preserve()
        cr.set_source_rgb(0, 0, 1)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        cr.move_to(blue.posx, blue.posy)
        cr.line_to(blue.posx + (5*math.cos(blue.orientation*math.pi/4)), blue.posy + (5*math.sin(blue.orientation*math.pi/4)))
        cr.set_line_width(2)
        cr.stroke()
    def draw_red_soldiers(self, cr, red):
        cr.set_line_width(1) #border width
        cr.set_source_rgb(0, 0, 0) #border color black
        cr.arc(red.posx, red.posy, 5, 0, 2*math.pi) #border shape and position (circle)
        cr.stroke_preserve() #draw border
        cr.set_source_rgb(1, 0, 0) #set color to red
        cr.fill() #fill border
        cr.set_source_rgb(0, 0, 0) #set color to black
        cr.move_to(red.posx, red.posy) #move to center of circle
        cr.line_to(red.posx + (5*math.cos(red.orientation*math.pi/4)), red.posy + (5*math.sin(red.orientation*math.pi/4))) #create line from center of circle to border in direction of soldier orientation
        cr.set_line_width(2)
        cr.stroke() #draw line indicating soldier orientation
    def draw_mortars(self, cr, mortar):
        cr.set_line_width(1)
        cr.set_source_rgb(0, 0, 0)
        cr.arc(mortar.posx, mortar.posy, 5, 0, 2*math.pi)
        cr.stroke_preserve()
        cr.set_source_rgb(0, 0, 1)
        cr.fill()
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(2)
        cr.move_to(mortar.posx, mortar.posy)
        cr.line_to(mortar.posx + 5, mortar.posy)
        cr.stroke()
        cr.move_to(mortar.posx, mortar.posy)
        cr.line_to(mortar.posx - 5, mortar.posy)
        cr.stroke()
        cr.move_to(mortar.posx, mortar.posy)
        cr.line_to(mortar.posx, mortar.posy + 5)
        cr.stroke()
        cr.move_to(mortar.posx, mortar.posy)
        cr.line_to(mortar.posx, mortar.posy - 5)
        cr.stroke()

class Simulation(gtk.Window):

    def __init__(self, input_file):
        #inherits from the gtk.Window class
        super(Simulation, self).__init__()

        self.set_title('Simulation')
        self.set_size_request(WIDTH, HEIGHT)
        #doesn't allow the user to resize the window
        self.set_resizable(False)
        #centers the window on the screen
        self.set_position(gtk.WIN_POS_CENTER)

        #TODO comment
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK)

        #create a SimArea object
        self.sim_area = SimArea(input_file)
        #create a key press event listener
        self.connect("key-press-event", self.on_key_down)#TODO TEMP?
        #create a key release event listener
        self.connect("key-release-event", self.on_key_up)#TODO TEMP?

        self.connect("button-press-event", self.on_mouse)

        #adds the SimArea to the Simulation window
        self.add(self.sim_area)

        #creates an event listener that kills the process when the window is detroyed
        self.connect("destroy", gtk.main_quit)
        #displays all gtk elements
        self.show_all()

    #####TEMP METHODS?######START
    def on_key_down(self, widget, event):
        print "("+str(event.x)+","+str(event.y)+")"
        key = event.keyval
        self.sim_area.on_key_down(event)

    def on_key_up(self, widget, event):
        key = event.keyval
        self.sim_area.on_key_up(event)

    def on_mouse(self, widget, event):
        print "("+str(event.x)+","+str(event.y)+")"
    #####TEMP METHODS?######END

class MortarShot:
    def __init__(self, s_x, s_y, t_x, t_y):
        '''
        @summary: a class to hold data for each mortar shot fired
        @param source_x: the x-coord for the source mortar
        @param source_y: the y-coord for the source mortar
        @param target_x: the x-coord for the target point
        @param target_y: the y-coord for the target point
        '''
        self.detonate = False #whether or not the mortar shot has detonated
        self.detonation_time = 1500 #1.5 seconds for explosion animation
        self.posx = s_x #x-position of mortar shot
        self.posy = s_y #y-position of mortar shot
        self.t_x = t_x #x-position of mortar target
        self.t_y = t_y #y-position of mortar target
        self.time_in_air = 20000
        dx = s_x - t_x
        dy = s_y - t_y
        dist = math.hypot(dx, dy)
        ticks_in_air = self.time_in_air / TIME_BETWEEN_FRAMES
        magnitude = dist / ticks_in_air
        theta = math.atan2(dy, dx)
        self.delta_x = math.cos(theta) * magnitude
        self.delta_y = math.sin(theta) * magnitude

    def update(self):
        if not self.detonate:
            self.posx -= self.delta_x
            self.posy -= self.delta_y
            self.time_in_air -= TIME_BETWEEN_FRAMES
            if self.time_in_air <= 0:
                self.detonate = True
        else:
            self.detonation_time -= TIME_BETWEEN_FRAMES



if __name__ == "__main__":
    Simulation(sys.argv[1])
    gtk.main()
