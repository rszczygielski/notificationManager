import os
import signal
import time
from argparse import ArgumentParser
from enum import Enum, auto
from mailManager import MailManager
from contacts.contacts import Contacts, Number, Email
from myLogger.myLogger import Logger


class User():
    def __init__(self, firstName, lastName):
        self.firstName = firstName
        self.lastName = lastName
    
    @classmethod
    def initFromString(cls, userString):
        userString = userString.strip()
        splitedUserString = userString.split()
        return cls(splitedUserString[0], splitedUserString[1])
    
    def __str__(self):
        return f'{self.firstName} {self.lastName}'

class NotificationManager(Contacts):
    def __init__(self):
        super().__init__("contacts.txt")
        self.activeUsers = []
        self.activeUsersFile = "active_users.txt"
        self.readActiveUsers()
    
    def saveDecorator(method):
        def wrapper(self, *args):
            result = method(self, *args)
            self.saveActiveContactsToFile()
            return result
        return wrapper

    @saveDecorator
    def addUserToActive(self, firstName, lastName):
        for activeUser in self.activeUsers:
            # if activeUser.firstName == firstName and activeUser.lastName == lastName:
            if activeUser == f"{firstName} {lastName}":
                Logger.ERROR("This active user already exist")
                return
        numberOfActiveUsers = len(self.activeUsers)
        for contact in self.contacts:
            if contact.firstName == firstName and contact.lastName == lastName:
                self.activeUsers.append(User(firstName, lastName))
                Logger.INFO(f"User {firstName} {lastName} added to active users")
        newNumberOfActiveUsers = len(self.activeUsers)
        if numberOfActiveUsers ==  newNumberOfActiveUsers:
            Logger.INFO("There is no such contact, add contact first than update active users")

    @saveDecorator
    def addUsersToActive(self, users:list):
        for user in users:
            if isinstance(user, User):
                self.addUserToActive(user.firstName, user.lastName)
        

    def sendMailToActiveUsers(self, sender, msg, subject):
        mailManager = MailManager(sender)
        for user in self.activeUsers:
            mailToSend = self.contacts.getDefaultEmail(user.firstName, user.lastName)
            mailManager.sendMail(msg, subject, mailToSend)

    def saveActiveContactsToFile(self):
        with open(self.activeUsersFile, "w") as activeUsersFile:
            for user in self.activeUsers:
                activeUsersFile.write(f'{user}\n')
    
    def readActiveUsers(self):
        with open(self.activeUsersFile) as activeUsersFile:
            for line in activeUsersFile.readlines():
                self.activeUsers.append(User.initFromString(line))
    
    def printActiveUsers(self):
        for activeUser in self.activeUsers:
            print(activeUser)

class TerminalUser(NotificationManager):
    def __init__(self):
        super().__init__()
    
    def terminalAddContact(self):
        firstName = input("First name: ")
        lastName = input("Last name: ")
        newNumber = input("New number: ")
        newEmail = input("New email: ")
        self.addContact(firstName, lastName, Number(newNumber), Email(newEmail))

    def terminalAddUserToActive(self):
        firstName = input("First Name: ")
        lastName = input("Last Name: ")
        self.addUserToActive(firstName, lastName)
    
    def terminalAddUsersToActive(self):
        try:
            numberOfUsers = int(input("How many users you want to add? "))
        except ValueError:
            print("Please enter a number")
            self.terminalAddUsersToActive()
        listOfUsers = []
        for _ in range(numberOfUsers):
            firstName = input("First Name: ")
            lastName = input("Last Name: ")
            listOfUsers.append(User(firstName, lastName))
        self.addUsersToActive(listOfUsers)
    
    def terminalSendMailToActiveUsers(self):
        sender = input("Enter sender email: ")
        messageToSend = input("Massage to send: ")
        subject = input("Enter a subject for the email: ")
        self.sendMailToActiveUsers(sender, messageToSend, subject)

    def terminalSaveActiveContactsToFile(self):
        self.saveActiveContactsToFile()
    
    def terminalPrintActiveUsers(self,):
        self.printActiveUsers()

    def exitTerminal(self):
        exit()

class Killer():
    def __init__(self):
        self.killer = False
        signal.signal(signal.SIGINT, self.handlerInterupt)
        signal.signal(signal.SIGTSTP, self.handlerTerminalStop)
    
    def handlerInterupt(self, *args):
        print("\tInterupt signal")
        self.killer = True
    
    def handlerTerminalStop(self, *args):
        print("\tStop terminal signal")
        self.killer = True

class ComendTerminal(Enum):
    ADD_CONTACT = auto()
    ADD_USER_TO_ACTIVE = auto()
    ADD_USERS_TO_ACTIVE = auto()
    SEND_EMAIL_TO_ACTIVE_USERS = auto()
    SAVE_ACTIVE_USERS_TO_FILE= auto()
    PRINT_ACTIVE_USERS = auto()
    EXIT = auto()

def terminalMode():
    terminal = TerminalUser()

    terminalCommandDict ={
        ComendTerminal.ADD_CONTACT.value: terminal.terminalAddContact,
        ComendTerminal.ADD_USER_TO_ACTIVE.value: terminal.terminalAddUserToActive,
        ComendTerminal.ADD_USERS_TO_ACTIVE.value: terminal.terminalAddUsersToActive,
        ComendTerminal.SEND_EMAIL_TO_ACTIVE_USERS.value: terminal.terminalSendMailToActiveUsers,
        ComendTerminal.SAVE_ACTIVE_USERS_TO_FILE.value: terminal.terminalSaveActiveContactsToFile,
        ComendTerminal.PRINT_ACTIVE_USERS.value: terminal.terminalPrintActiveUsers,
        ComendTerminal.EXIT.value: terminal.exitTerminal,
    }

    textInput = "\n"
    for command in ComendTerminal:
        textInput += f"\tPress {command.value} to {command.name}\n"
    
    while True:
        Logger.settings(show_date=False, show_file_name=False)
        try:
            userInput = int(input(textInput))
        except ValueError:
            Logger.ERROR("WRONG INPUT VALUE")
        try:
            terminalCommandDict[userInput]()
        except KeyError:
            Logger.ERROR("WRONG INPUT VALUE")

def notificationMode(notificationDirPath):
    notificationManager = NotificationManager()
    killerInstance = Killer()
    while not killerInstance.killer:
        listOfFiles = os.listdir(notificationDirPath)
        for notificationFile in listOfFiles:
            notificationFilePath = os.path.join(notificationDirPath, notificationFile)
            with open(notificationFilePath) as readFile:
                message = readFile.read()
            notificationManager.sendMailToActiveUsers("radek.szczygielski.trash@gmail.com", message, notificationFile)
            os.remove(notificationFilePath)
        time.sleep(0.1)

if __name__ == "__main__":
    parser = ArgumentParser("Notification Manager for sending emails")
    parser.add_argument("-i", "--interactive", dest= "interactive_mode", action="store_true", help="Turn on the interactive mode")
    arg = parser.parse_args()
    interactiveMode = arg.interactive_mode
    if interactiveMode:
        terminalMode()
    else:
        notificationMode("/home/rszczygielski/pythonVSC/personal_classes/notificationManager/notifications")