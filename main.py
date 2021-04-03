import json
#import urllib.request, json
import requests
from tkinter import *
from tkinter import ttk
from tkinter.ttk import *
from ttkthemes import ThemedStyle
from ctypes import windll, byref, create_unicode_buffer, create_string_buffer
from PIL import ImageTk, Image
import win32api
import subprocess
import threading
import queue
import os
import re
from os import system
from re import sub
import sys


os.environ["PYTHONUNBUFFERED"] = "1"
FR_PRIVATE  = 0x10
FR_NOT_ENUM = 0x20


def enqueue_output(p, q):
    while True:
        out = p.stdout.readline()
        if out == '' and p.poll() is not None:
            break
        if out:
            #print(out.strip(), flush=True)
            q.put_nowait(out.strip())


def loadfont(fontpath, private=True, enumerable=False):
    '''
    Makes fonts located in file `fontpath` available to the font system.

    `private`     if True, other processes cannot see this font, and this 
                  font will be unloaded when the process dies
    `enumerable`  if True, this font will appear when enumerating fonts

    See https://msdn.microsoft.com/en-us/library/dd183327(VS.85).aspx

    '''
    # This function was taken from
    # https://github.com/ifwe/digsby/blob/f5fe00244744aa131e07f09348d10563f3d8fa99/digsby/src/gui/native/win/winfonts.py#L15
    # This function is written for Python 2.x. For 3.x, you
    # have to convert the isinstance checks to bytes and str
    if isinstance(fontpath, bytes):
        pathbuf = create_string_buffer(fontpath)
        AddFontResourceEx = windll.gdi32.AddFontResourceExA
    elif isinstance(fontpath, str):
        pathbuf = create_unicode_buffer(fontpath)
        AddFontResourceEx = windll.gdi32.AddFontResourceExW
    else:
        raise TypeError('fontpath must be of type str or unicode')

    flags = (FR_PRIVATE if private else 0) | (FR_NOT_ENUM if not enumerable else 0)
    numFontsAdded = AddFontResourceEx(byref(pathbuf), flags, 0)
    return bool(numFontsAdded)

def resource_path(relative_path):    
    try:       
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def GetWalletHash(self):
    myCookies = dict(wa=self.curAddress.get())

    data = json.loads(requests.get(self.stats, cookies=myCookies).text)

    rate = data["miner_hashrate"]
    return "Hashrate: {0:.2f} KH/s".format(float(rate)/1000)

class Window(Frame):

    MAX_CORES = os.cpu_count() - 2
    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.started = False
        self.p = None
        self.q = queue.Queue()
        self.threads = 2
        self.statsRefreshRate = 30000

        self.vibeStatuses = ['Vibin\'', 'Groovin\'', 'Ragin\'']

        with open(resource_path('ragehaus.json')) as fp:
            data = json.load(fp)

        self.pool = data["pool"]
        self.stats = data["stats"]

        self.wallets = data["wallets"]
        self.WalletNames = [i.get('name') for i in self.wallets]

        self.curWalletIndex = 1;
        self.curWallet = StringVar()
        self.curWallet.set(self.wallets[self.curWalletIndex]["name"])

        self.curAddress= StringVar()
        self.curAddress.set(self.wallets[self.curWalletIndex]["address"])

        self.curWalletImage = ImageTk.PhotoImage(Image.open(resource_path(self.wallets[self.curWalletIndex]["image"])).resize((50,50), Image.ANTIALIAS))

        #self.walletHash = StringVar()
        #self.walletHash.set(GetWalletHash(self))

        self.idleCheck = IntVar()
        self.lastInput = StringVar()
        self.lastInput.set("0")
        self.idleCounter = 0
        self.idleStart = False

        #self.hugepagesCheckbuttonVar = IntVar()
        #self.wowneroRadiobuttonVar = IntVar()

        self.init_window()
        
    def RefreshWalletHash(self):
        myCookies = dict(wa=self.curAddress.get())

        data = json.loads(requests.get(self.stats, cookies=myCookies).text)

        rate = data["miner_hashrate"]
        self.walletHash.set("Hashrate: {0:.2f} KH/s".format(float(rate)/1000))
        self.walletHashlbl.after(self.statsRefreshRate, self.RefreshWalletHash)

    #triggers every 5 seconds, runs after 60 loops -- 5 mins
    def RefreshIdleTime(self):
        thisInput = str(win32api.GetLastInputInfo())
        lastIn = self.lastInput.get()
        if thisInput == self.lastInput.get():
            self.idleCounter += 1
        else:
            self.idleCounter = 0
            self.lastInput.set(thisInput)

        if self.idleCounter >= 36 and not self.started and self.idleCheck.get() == 1:
            self.idleStart = True
            self.startstop()
        elif self.idleCounter < 36 and self.idleStart:
            self.idleStart = False
            self.startstop()

        self.idleTimelbl.after(5000, self.RefreshIdleTime)

    def init_window(self):
        
        self.master.title("Rage Haush")
        self.pack(fill=BOTH, expand=1)
        self.titleLabel = Label(self, text="Rage Haush")

        addrFrameX = winWidth*0.05
        addrFrameY = winHeight*0.05
        addrFrameWidth = winWidth*0.9
        addrFrameHeight = winWidth*0.3
        threadFrameX = winWidth*0.05
        threadFrameY = winHeight*0.45
        threadFrameWidth = winWidth*0.9
        threadFrameHeight = winWidth*0.22
        
        #--- ADDRESS FRAME
        self.addrFrame = LabelFrame(width=addrFrameWidth, height = addrFrameHeight, text="Receiving Address");
        self.addrFrame.pack()
        self.addrFrame.place(x=addrFrameX, y=addrFrameY)

        self.walletAddress = Entry(self.addrFrame, textvariable=self.curAddress, width=52)
        self.walletAddress.pack()
        self.walletAddress.place(x = addrFrameWidth*0.05, y = addrFrameHeight*0.6)
        self.walletAddress.config(state=DISABLED)
        

        self.walletImage = Label(self.addrFrame, image=self.curWalletImage, background="#414141")
        self.walletImage.image = self.curWalletImage
        self.walletImage.place(x=addrFrameWidth*0.05, y=threadFrameHeight*0.1)
        
        self.walletName = Label(self.addrFrame, textvariable=self.curWallet,font=("AmazDooMLeft", 30), background="#414141")
        self.walletName.pack()
        self.walletName.place(x=addrFrameWidth*0.20, y=threadFrameHeight*0.12)

        #self.walletHashlbl = Label(self.addrFrame, textvariable=self.walletHash, background="#414141")
        #self.walletHashlbl.pack()
        #self.walletHashlbl.place(x=addrFrameWidth*0.20, y=threadFrameHeight*0.55)
        #self.walletHashlbl.after(self.statsRefreshRate, self.RefreshWalletHash)

        #doesn't display anthing, just runs updater function
        self.idleTimelbl = Label(self.addrFrame)
        self.idleTimelbl.after(5000, self.RefreshIdleTime)

        #---THREAD FRAME
        self.threadFrame = LabelFrame(width=threadFrameWidth, height = threadFrameHeight, text="Local Hashrate");
        self.threadFrame.pack()
        self.threadFrame.place(x=threadFrameX, y=threadFrameY)

        self.hashRateLabel = Label(self.threadFrame, text="0.00 KH/s", background="#414141")
        self.hashRateLabel.pack()
        self.hashRateLabel.place(x=threadFrameWidth*0.05, y=threadFrameHeight*0.1)
        self.hashRateLabel.after(2000, self.refresh_hashrate)

        self.hashStatus = Label(self.threadFrame, text=self.vibeStatuses[0], background="#414141")
        self.hashStatus.pack()
        self.hashStatus.place(x=threadFrameWidth*0.85, y=threadFrameHeight*0.1)

        self.threadSlider = Scale(self.threadFrame, from_= 2, to=self.MAX_CORES, orient=HORIZONTAL, length=threadFrameWidth*0.95,  command=self.thread_count_change)
        self.threadSlider.pack()
        self.threadSlider.place(x=threadFrameWidth*0.025, y=threadFrameHeight*0.3)
       

        self.threadLabel = Label(self.threadFrame, text="Thread Count: ", background="#414141")
        self.threadLabel.pack()
        self.threadLabel.place(x=threadFrameWidth*0.05, y=threadFrameHeight*0.56)

        self.threadCountlbl = Label(self.threadFrame, text="2", background="#414141")
        self.threadCountlbl.pack()
        self.threadCountlbl.place(x=threadFrameWidth*0.05 + 85, y=threadFrameHeight*0.56)

      

        #---Mine To
        self.mineTolbl = Label(self, text = "Mine to: ")
        self.mineTolbl.pack()
        self.mineTolbl.place(x=threadFrameX, y=threadFrameY + threadFrameHeight + 16)
        self.WalletMenu = OptionMenu(self, self.curWallet, *self.WalletNames, command=self.ChangeMineTo)
        self.WalletMenu.pack()
        self.WalletMenu.place(x=threadFrameX + 50, y=threadFrameY + threadFrameHeight + 10 )

        #self.outputLabelLabel = Label(self, text="Miner output:")
        self.outputLabel = Label(self, text="")
        #self.outputLabelLabel.place(x=winWidth*0.05, y=270)
        self.outputLabel.place(x=winWidth*0.05, y=threadFrameY + threadFrameHeight + 48)

        #---On/Off
        self.startButton = Button(self, text="Start", command=self.startstop, width = 10)
        self.quitButton = Button(self, text="Quit", command=self.client_exit, width = 10)
        self.startButton.place(x=winWidth*0.5 + 3,  y=threadFrameY + threadFrameHeight + 10)
        self.quitButton.place(x=winWidth*0.5 + 95, y=threadFrameY + threadFrameHeight + 10)
        
        self.idleChk = Checkbutton(self, text="Run Idle                ", variable=self.idleCheck, onvalue=1, offvalue=0, command=self.idleCheckOnoff)
        self.idleChk.place(x=winWidth*0.5 + 95, y=threadFrameY + threadFrameHeight + 42)
      

        self.threadSlider.set(2)
#`````````````````````````````````````````````````````````````````````````````````````
    def idleCheckOnoff(self):
        if self.idleCheck.get() == 1 :
            self.threadSlider.config(state=DISABLED)
            self.WalletMenu.config(state=DISABLED)
            self.walletAddress.config(state=DISABLED)
            self.startButton.config(state=DISABLED)
        else:
            self.threadSlider.config(state=ACTIVE)
            self.WalletMenu.config(state=ACTIVE)
            self.startButton.config(state=ACTIVE)
            if self.wallets[self.curWalletIndex]["custom"]:
                self.walletAddress.config(state=NORMAL)
  

    def ChangeMineTo(self,val):
        x = 0
        walletLen = len(self.WalletNames)
        for i in range(0, walletLen):
            if self.WalletNames[i] == val:
                x = i
                break

        if x == 0:
            return
        self.curWalletIndex = x
        self.curAddress.set(self.wallets[x]["address"])
        self.curWallet.set(self.wallets[x]["name"])
        
        if(self.wallets[x]["custom"]):
            self.walletAddress.config(state=NORMAL)
        else :
            self.walletAddress.config(state=DISABLED)

        self.curWalletImage = ImageTk.PhotoImage(Image.open(resource_path(self.wallets[x]["image"])).resize((50,50), Image.ANTIALIAS))
        self.walletImage.configure(image = self.curWalletImage)
        #self.walletHash.set(GetWalletHash(self))

    def startstop(self):
        if not self.started:
            try:
                self.threads = int(self.threadSlider.get())                
            except:
                self.threads = 2
            if self.threads > self.MAX_CORES:  
                self.threads = self.MAX_CORES
            #self.threadsEntry.delete(0, 'end')
            #self.threadsEntry.insert(0, self.threads)
            self.threadSlider.config(state=DISABLED)
            self.WalletMenu.config(state=DISABLED)
            self.walletAddress.config(state=DISABLED)
            if self.idleCheck.get() == 0:
                self.idleChk.config(state=DISABLED)
            #if self.hugepagesCheckbuttonVar.get():
            hugepages = ""
            #else:
            #    hugepages = "--no-huge-pages"
            print(self.threads)
            #if self.wowneroRadiobuttonVar.get() == 1 or self.wowneroRadiobuttonVar.get() == 3:
            algo = "rx/wow"
            #else: 
                #algo = "rx/0"
            self.p = subprocess.Popen([resource_path("xmrig.exe"), "-t", str(self.threads), 
                        hugepages, "--donate-level=0", "--cpu-priority=0", "-a", algo, "-o", str(self.pool), "-u", str(self.curAddress.get())],
                        #stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        #shell=False,
                        encoding='utf-8',
                        #creationflags=0x08000000,
                        errors='replace')
            self.t = threading.Thread(target=enqueue_output, args=(self.p, self.q))
            self.t.daemon = True
            self.t.start()
            self.started = True
            #if self.threads < 3:
            #    self.statusImage = Label(image=self.imgStarted)
            #    self.statusImage.image = self.imgStarted
            #else:
            #    self.statusImage = Label(image=self.imgVeryStarted)
            #    self.statusImage.image = self.imgVeryStarted
            #self.statusImage.place(x=140, y=100)
            #self.statusLabel.config(text="Current status:\nMining")
            self.startButton.config(text="Stop")
        elif self.started:
            system("taskkill /im xmrig.exe /f")
            self.p.kill()
            self.t.join()
            self.outputLabel.config(text="")
            self.started = False
            #self.statusImage = Label(image=self.imgStopped)
            #self.statusImage.image = self.imgStopped
            #self.statusImage.place(x=140, y=100)
            #self.statusLabel.config(text="Current status:\nNot mining")
            self.hashRateLabel.config(text="Hashrate: 0.00 KH/s")
            self.startButton.config(text="Start")
            if self.idleCheck.get() == 0:
                self.threadSlider.config(state=ACTIVE)
                self.WalletMenu.config(state=ACTIVE)
                self.idleChk.config(state=ACTIVE)
                if self.wallets[self.curWalletIndex]["custom"]:
                    self.walletAddress.config(state=NORMAL)

    #def refresh_wallet_hash(self):
    #    with urllib.request.urlopen("http://puddle.freak.farm:4243/stats/" + self.curAddress.get()) as url:
    #        data = json.loads(url.read().decode())

    #    self.walletHash.set("Hashrate: {0:.2f} KH/s".format(float(data["miner_hashrate"])/1000))

    def refresh_hashrate(self):
        if not self.started:
            pass
        elif self.started:
            try:
                line = self.q.get_nowait()
                print(line)
                if len(line) > 5:
                    self.outputLabel.config(text=line)
                try:
                    if "speed" in line:
                        hashrate = re.findall(" \d+\.\d+ ", line)[0]
                        self.hashRateLabel.config(text="Hashrate: {0:.2f} KH/s".format(float(hashrate)/1000))
                except:
                    pass
            except:
                pass
        self.hashRateLabel.after(1000, self.refresh_hashrate)

    def thread_count_change(self, val):
        self.threads = round(float(val))
        self.threadCountlbl.config(text=str(self.threads))
        if self.threads >= round(self.MAX_CORES * 4 / 5):
            self.hashStatus.config(text=self.vibeStatuses[2])
        elif self.threads >= round (self.MAX_CORES / 2):
            self.hashStatus.config(text=self.vibeStatuses[1])
        else:
            self.hashStatus.config(text=self.vibeStatuses[0])

    def client_exit(self):
        try:
            system("taskkill /im xmrig.exe /f")
            self.p.kill()
            self.t.join()
        except:
            pass
        sys.exit(0)

#Set general Window style
winWidth = 400
winHeight = 300
clrBlack = '#000000'
clrPurple = '#a430c5'
clrTeal = '#43d5f9'

loadfont(resource_path("AmazDooM.ttf"))

root = Tk()
root.iconbitmap(default=resource_path('haush.ico'))
#root.overrideredirect(True) # turns off title bar, geometry
root.geometry(str(winWidth)+"x"+str(winHeight)+"+300+300")
root.resizable(width=False, height=False)

app = Window(root)

style = ThemedStyle(app)
#style.set_theme("equilux")
style.theme_use('equilux')

root.mainloop()

