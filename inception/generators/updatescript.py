from generator import Generator
import os
class UpdateScriptGenerator(Generator):

    HEADER_INCEPTION = """
.__                            __             .___
|__| ____   ____  ____ _______/  |_  ____   __| _/
|  |/    \_/ ___\/ __ \\____ \   __\/ __ \ / __ | 
|  |   |  \  \__\  ___/|  |_> >  | \  ___// /_/ | 
|__|___|  /\___  >___  >   __/|__|  \___  >____ | 
        \/     \/    \/|__|             \/     \/ 
"""

    def __init__(self):
        super(UpdateScriptGenerator, self).__init__()
        self.commands = []
        self.dirty = False
        self.header = """
..######..##.....##.####.########.########.########.....###....########.
.##....##.##.....##..##.....##....##.......##.....##...##.##...##.....##
.##.......##.....##..##.....##....##.......##.....##..##...##..##.....##
..######..##.....##..##.....##....######...########..##.....##.##.....##
.......##.##.....##..##.....##....##.......##........#########.##.....##
.##....##.##.....##..##.....##....##.......##........##.....##.##.....##
..######...#######..####....##....########.##........##.....##.########.
"""
    
    def isDirty(self):
        return self.dirty

    def setHeader(self, header):
        self.header = header

    def getHeaderCommands(self, header = None):
        header = header or self.header
        commands = []
        if header is None: return commands
        headerLines = header.split("\n")
        for l in headerLines:
            commands.append(self._genCmd("ui_print", self._quote(l)))

        return commands


    def mount(self, mountPoint):
        self.run("/sbin/mount", mountPoint)

    def echo(self, text):
        self._add("ui_print", self._quote(text))

    def rm(self, path, recursive = False):
        self.dirty = True
        if recursive:
            self._add("delete_recursive", self._quote(path))
        else:
            self._add("delete", self._quote(path))

    def run(self, *args):
        if not args[0].endswith("/mount"):
            self.dirty = True
        self._add("run_program", *(self._quote(a) for a in args))

    def writeImage(self, path, blockDevice):
        self.dirty = True
        #fname = os.path.basename(path)
        #tmpExt = "/tmp/" + fname
        #self.extractFile(path, tmpExt)
        #self._add("write_raw_image", self._quote(tmpExt), self._quote(blockDevice))
        self.run("/sbin/busybox", "dd", "if=%s" % path, "of=%s" % blockDevice)

    def extractFile(self, f, out):
        self.dirty = True
        self._add("package_extract_file", self._quote(f), self._quote(out))

    def extractDir(self, dir, out):
        self.dirty = True
        self._add("package_extract_dir", self._quote(dir), self._quote(out))

    def setPermissions(self, path, uid, gid, fmode, dmode = None):
        self.dirty = True
        if dmode is None:
            self._add("set_perm", uid, gid, fmode, self._quote(path))
        else:
            self._add("set_perm_recursive", uid, gid, dmode, fmode, self._quote(path))

    def _quote(self, string):
        return "\"%s\"" % string

    def _genCmd(self, *args):
        cmd = args[0]
        cmdArgs = args[1:]
        cmdTmpl="{cmd}({args});"
        return cmdTmpl.format(cmd = cmd, args = ", ".join(cmdArgs))
    
    def _add(self, *args):
        cmd = self._genCmd(*args)
        if args[0] != "ui_print":
            self.echo(cmd.replace("\"","'"))
        self.commands.append(cmd)

    def _genProgress(self, total, done):
        val = "%.6f" % (float(done)/float(total))

        return self._genCmd("set_progress", val)

    def generate(self):
        headerCommands = self.getHeaderCommands()
        commandsProgressified = []
        total = len(self.commands)
        lastProgress = ""
        for i in range(0, total):
            c = self.commands[i]
            progress = self._genProgress(total, i)

            if progress != lastProgress:
                lastProgress = progress
                commandsProgressified.append(progress)

            commandsProgressified.append(c)

        commands = headerCommands + commandsProgressified + self.getHeaderCommands(self.__class__.HEADER_INCEPTION)
        
        for i in range(0, 5):
            commands.append(self._genCmd("ui_print", self._quote("#")))

        # commands.append(self._genCmd("sleep", "15"))
        return "\n".join(commands)

