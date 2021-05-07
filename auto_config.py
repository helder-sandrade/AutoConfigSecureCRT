#$language = "python"
#$interface = "1.0"
import re

PORTS = 5000
MAX_PORTS = 50

DEFAULT_COMMANDS = [
    'terminal len 0',
    'show ip int br',
    'conf t',
    'ipv6 unicast-routing',
    'username cisco priv 15 pass cisco',
    'line vty 0 4',
    'login local',
    'end',
]

class AutoConfig:

    def __init__(self, eCount=1, prefix=200):
        self.eCount = eCount
        self.tab = crt.GetScriptTab()
        self.tab.Screen.Synchronous = False
        self.hostname = None
        self.prefix = prefix

    #Usado para gravar os logs em arquivo, uso futuro
    def record(self, texto):
        f = open('saida.txt', 'w')
        f.write(texto)
        f.close()

    #Usado para emitir avisos, uso futuro
    def msg(self, txt):
        crt.Dialog.MessageBox(txt)

    #sleep
    def sleep(self, timer=1):
        crt.Sleep(100*timer)

    #Obtem o hostname do equipamento que está sendo acesso
    def Gethostname(self):
        row = self.tab.Screen.CurrentRow
        column = self.tab.Screen.CurrentColumn - 1
        prompt = self.tab.Screen.Get(row, 0, row, column)
        prompt = prompt.strip()
        return prompt

    #Cria uma configuração inicial
    def ExecDefaultConfig(self, commands):
        self.tab.Screen.Send('\r')
        ret = self.tab.Screen.WaitForStrings(['#'], 10)
        self.hostname = self.Gethostname()
        if ret:
            for command in commands:
                #self.sleep(1)
                self.tab.Screen.Send(command)
                self.tab.Screen.Send('\r')
                ret = self.tab.Screen.WaitForStrings(['#'], 15)

    #Executa comandos
    def SendCommand(self, command):
        self.tab.Screen.Send('\r')
        ret = self.tab.Screen.WaitForStrings(['#'], 10)
        if ret:
            #self.sleep(1)
            self.tab.Screen.Send(command)
            self.tab.Screen.Send('\r')
            ret = self.tab.Screen.WaitForStrings(['#'], 10)

    #Recebe o retorno do comando para processar
    def GetCommand(self, command):
        self.tab.Screen.Send('\r')
        ret = self.tab.Screen.WaitForStrings(['#'], 10)
        if ret:
            self.tab.Screen.Send(command)
            self.tab.Screen.Send('\r')
            ret = self.tab.Screen.ReadString(self.hostname)
            return ret
        return None

    #Efetua a configura das portas que estão com cdp habilitado
    def ConfigureInterface(self):
        reg = r"(R\d+)\s+(\S+ \S+)\s+\d+.*"
        out = self.GetCommand('show cdp neighbors')
        #self.sleep(3)
        self.SendCommand('configure terminal')
        if out is not None:
            lines = out.splitlines()
            for line in lines:
                r = re.match(reg,line)
                if r:
                    host = int(self.hostname[1:-1])
                    min = int(self.hostname[1:-1])
                    max = int(r.group(1)[1:])
                    if min > max:
                        min,max = max,min
                    ip = 'ip add prefix.min.max.host 255.255.255.0'
                    ip = re.sub('prefix', str(self.prefix), ip)
                    ip = re.sub('min', str(min), ip)
                    ip = re.sub('max', str(max), ip)
                    ip = re.sub('host', str(host), ip)
                    ipv6 = 'ipv6 address 2001:DB8:min:max:host:host:host:host/64'
                    ipv6 = re.sub('min', str(min), ipv6)
                    ipv6 = re.sub('max', str(max), ipv6)
                    ipv6 = re.sub('host', str(host), ipv6)
                    interface = 'interface intf'
                    interface = re.sub('intf', r.group(2), interface)
                    self.SendCommand(interface)
                    self.SendCommand(ip)
                    self.SendCommand(ipv6)
                    ip = 'ip add host.host.host.host 255.255.255.255'
                    ip = re.sub('host', str(host), ip)
                    ipv6 = 'ipv6 address 2001:DB8:host:host:host:host:host:host/128'
                    ipv6 = re.sub('host', str(host), ipv6)
                    interface = 'interface lo0'
                    self.SendCommand(interface)
                    self.SendCommand(ip)
                    self.SendCommand(ipv6)
        self.SendCommand('end')
        self.SendCommand('wr')
        
    #Executa a configuração equipamento por equipamento
    def Configure(self):
        for i in range(MAX_PORTS):
            crt.Session.Disconnect()
            crt.Session.Connect('/telnet 127.0.0.1 ' + str(PORTS+i) , failSilently=True)
            if crt.Session.Connected:
                self.sleep(2)
                self.ExecDefaultConfig(DEFAULT_COMMANDS)
                self.ConfigureInterface()
                self.eCount -= 1
                if self.eCount == 0:
                    break
            if i == MAX_PORTS:
                break


equipamentos = int(crt.Dialog.Prompt('Quantos equipamentos existem no lab', 'Equipamentos', '1', False))
prefixo = int(crt.Dialog.Prompt('Qual o prefixo que sera utilizado', 'Prefixo', '200', False))

if equipamentos > 0:
    a = AutoConfig(eCount=equipamentos,prefix=prefixo)
    a.Configure()