#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import randrange, seed
import socket
import sys
import threading
from datetime import datetime
from math import *


class Rendezvous:

    def __init__(self, arquivoConfiguracoes):

        """
        Lendo o arquivo de configuracoes onde a primeira linha contem um
        numero 0 ou 1 que representa o modulo. Modulo 0 os IDs sao os numeros
        inteiros entre [0,K] e modulo 1 os IDs sao as potencias de 2 entre
        [2,K]. A segunda linha do arquivo de configuracoes determina o K
        """
        f = open(arquivoConfiguracoes, 'r')
        self.configID = int(f.readline())
        self.K = int(f.readline())
        f.close()

        """
        Inicializa o dicionario que guarda a lista de IDs e seus respectivos
        enderecos
        """
        self.listaIDs = {}

        self.rootNodeID = -1
        self.HOST = ''
        self.PORT = 12000
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind((self.HOST, self.PORT))

    """
    Metodo que gera o ID aleatorio segundo o modulo escolhido no arquivo de
    configuracoes
    """
    def geraID(self):
        seed(datetime.now())
        ID = None

        """
        Modulo 0, gera aleatoriamente um ID valido ate encontrar um que nao
        esteja sendo utilizado
        """
        if self.configID == 0:
            ID = randrange(0, self.K)
            while ID in self.listaIDs:
                ID = randrange(0, self.K)

        elif self.configID == 1:
            """
            Modulo 1, gera aleatoriamente um ID valido ate encontrar um que nao
            esteja sendo utilizado
            """

            lim = int(log(self.K)/log(2))
            ID = 2 ** randrange(1, lim+1)
            while ID in self.listaIDs:
                ID = 2 ** randrange(1, lim+1)

        return ID

    """
    Metodo que interpreta os dados recebidos e envia(ou nao) uma resposta
    """
    def processaDados(self, dados, enderecoCliente):

        # Mensagem que indica que um novo no deseja se cadastrar na rede
        if dados == 'hello':

            # Se a rede nao estiver cheia, gera e envia o ID do novo no na rede
            if (self.configID == 0 and len(self.listaIDs) < self.K) or \
                (self.configID == 1 and len(self.listaIDs) <
                    int(log(self.K)/log(2))):
                self.s.sendto('0'+repr(self.geraID()), enderecoCliente)

        # Se a mensagem recebida for mensagem de confirmacao de ID
        elif dados[:9] == 'confirmID':
            nodeID = int(dados[9:])

            """
            Se o ID solicitado ainda estiver disponivel, insere o no na rede e
            envia confirmacao
            """
            if nodeID not in self.listaIDs.keys():
                self.listaIDs[nodeID] = enderecoCliente

                """
                Se a lista de IDs na rede esta vazia, o novo no sera o root
                node e a confirmacao e enviada
                """
                if self.rootNodeID == -1:
                    self.rootNodeID = nodeID
                    self.s.sendto('1RIDconfirmed', enderecoCliente)

                elif (self.configID == 0 and len(self.listaIDs) <= self.K) \
                    or (self.configID == 1 and len(self.listaIDs) <=
                        int(log(self.K)/log(2))):
                    """
                    Se ainda houver espaco na rede e enviada a confirmacao
                    para o novo no
                    """

                    self.s.sendto('1NIDconfirmed', enderecoCliente)

                self.exibeStatusRede()

            elif self.listaIDs[nodeID] == enderecoCliente:
                """
                Se o ID solicitado ja esta inserido na rede para o mesmo
                cliente, reenvia confirmacao
                """

                """
                Se ainda houver espaco na rede e enviada a confirmacao para o
                no novamente
                """
                if (self.configID == 0 and len(self.listaIDs) <= self.K) or \
                    (self.configID == 1 and len(self.listaIDs) <=
                        int(log(self.K)/log(2))):

                    if self.rootNodeID == nodeID:
                        self.s.sendto('1RIDconfirmed', enderecoCliente)
                    else:
                        self.s.sendto('1NIDconfirmed', enderecoCliente)

                self.exibeStatusRede()

        elif dados == 'root?':
            """
            Caso seja solicitado o endereco do root node, o rendesvouz envia-o
            se houver
            """

            if self.listaIDs != {}:
                enderecoRoot = self.listaIDs[self.rootNodeID]
                self.s.sendto('2'+repr(enderecoRoot), enderecoCliente)

        elif dados[:7] == 'nodeOff':
            nodeIDs = (dados[7:]).split('|')
            leavingNodeID = int(nodeIDs[0])
            senderID = int(nodeIDs[1])
            if leavingNodeID in self.listaIDs.keys():
                if leavingNodeID == self.rootNodeID:
                    del self.listaIDs[leavingNodeID]
                    self.s.sendto('3RnodeRemoved', enderecoCliente)
                    self.rootNodeID = senderID
                else:
                    del self.listaIDs[leavingNodeID]
                    self.s.sendto('3NnodeRemoved', enderecoCliente)

            self.exibeStatusRede()

    """
    Exibe a lista de Nos cadastrados na rede assim como os seus respectivos
    enderecos
    """
    def exibeStatusRede(self):
        print u'IDs cadastrados na rede: ' + repr(self.listaIDs)
        print u'ID do Root Node:'+repr(self.rootNodeID)

    """
    Metodo que ativa o servidor para escuta de novos quadros e consequente
    interacao
    """
    def iniciaServidor(self):
        print u"Rendezvous está de pé !"
        while True:
            dados, enderecoCliente = self.s.recvfrom(1024)
            t = threading.Thread(target=self.processaDados,
                                 args=(dados, enderecoCliente, ))
            t.start()
            t.join()


if __name__ == "__main__":

    # Inicializando um rendezvous com o command-line argumemt
    server = Rendezvous(sys.argv[1])
    server.iniciaServidor()

