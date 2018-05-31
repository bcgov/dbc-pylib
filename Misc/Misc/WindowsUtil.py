'''
Created on Dec 11, 2014

@author: kjnether

bunch of utility functions for dealing with windows paths
mounting drives etc.
'''

import string
import os.path
import win_unc

class WinPaths():
    def __init__(self):
        pass
    
    def getNextUnUsedDriveLetter(self, skipLetters=[]):
        skipLettersCaps = []
        for i in skipLetters:
            skipLettersCaps.append( i.upper() )
        alphabet = string.ascii_uppercase
        retLet = None
        for letter in alphabet:
            if not letter in skipLettersCaps:
                if not self.isLetterMapped(letter):
                    retLet = letter
                    break
        return retLet
    
    def mount(self, letter, uncstr):
        if letter[len(letter) - 1] <> ':':
            letter = letter + ':'
        #print 'letter:',letter
        mnt = win_unc.UncDirectoryMount(win_unc.UncDirectory(uncstr), win_unc.DiskDrive(letter))
        mnt.mount()
        #uncMnt.mount()
        
    def unMount(self, letter, uncstr):
        if letter[len(letter) - 1] <> ':':
            letter = letter + ':'
        mnt = win_unc.UncDirectoryMount(win_unc.UncDirectory(uncstr), win_unc.DiskDrive(letter))
        mnt.unmount()
            
    def isLetterMapped(self, letter):
        if os.path.exists(letter + ':'):
            retVal = True
        else:
            retVal = False
        return retVal
            
