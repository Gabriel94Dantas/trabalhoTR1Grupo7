#!/usr/bin/python
# -*- coding: utf-8 -*-

from socket import *
import sys


class Node:

    def __init__(self):

        # Substituir pelo (IP, PORTA) da maquina que executa o Rendezvous
        self.enderecoRendezvous = ('192.168.1.8', 12000)

        self.s = socket(AF_INET, SOCK_DGRAM)
        self.meuID = -1
        self.souRootNode = False
        self.rootAddr = -1

    """
    Esse metodo estabelece conexao com o rendezvous. Apos o metodo, se
    concluido com sucesso (retorna True), o no recebe um ID valido na rede,
    e informado se ele e ou nao o root node
    """
    def conectaRendezvous(self):

        numeroTentativas = 10

        # A primeira mensagem para o rendezvous e um simples hello
        self.s.sendto('hello', self.enderecoRendezvous)

        # O timer foi definido como meio segundo para cada tentativa
        self.s.settimeout(0.5)

        # Tenta 10 vez obter uma resposta do rendezvous
        while numeroTentativas > 0:
            try:
                msg, servAddr = self.s.recvfrom(1024)

                """
                Caso ele tenha recebido a resposta do rendezvous, ela sera o
                seu ID na rede
                """
                self.meuID = int(msg)
                break
            except timeout:
                if numeroTentativas != 1:
                    self.s.sendto('hello', self.enderecoRendezvous)
                numeroTentativas -= 1

        """
        Se nao conseguiu se comunicar com o rendezvous em 10 tentativas,
        desiste (retorna False)
        """
        if numeroTentativas == 0:

            # Antes de retornar, volta o socket para o modo sem timer
            self.s.setblocking(1)
            return False

        numeroTentativas = 10

        # A proxima mensagem e uma confirmacao do ID recebido do rendezvous
        self.s.sendto('confirmID' + repr(self.meuID), self.enderecoRendezvous)

        # Tenta 10 vez obter uma resposta do rendezvous
        while numeroTentativas > 0:
            try:
                msg, servAddr = self.s.recvfrom(1024)

                """
                Resposta recebida do rendezvous caso o no for o primeiro nao
                haja outros nos na rede (root node)
                """
                if msg == 'RIDconfirmed':
                    self.souRootNode = True
                    break

                elif msg == 'NIDconfirmed':
                    """
                    Resposta recebida do rendezvous caso existirem outros nos
                    na rede
                    """

                    self.souRootNode = False
                    break
                else:
                    numeroTentativas -= 1
                    break
            except timeout:
                if numeroTentativas != 1:
                    self.s.sendto('confirmID' + self.meuID,
                                  self.enderecoRendezvous)
                numeroTentativas -= 1

        """
        Se nao conseguiu se comunicar com o rendezvous em 10 tentativas,
        desiste (retorna False)
        """
        if numeroTentativas == 0:

            # Antes de retornar, volta o socket para o modo sem timer
            self.s.setblocking(1)
            return False

        # Antes de retornar, volta o socket para o modo sem timer
        self.s.setblocking(1)
        return True

    """
    Metodo que pede ao rendezvous o endereco do root node e deve ser usado
    toda vez que for necessario fazer a comunicacao com o root node (pois este
    pode subitamente sair da rede)
    """
    def pedeEnderecoRootNode(self):

        # O metodo so e necessario caso o no nao seja o root node
        if not self.souRootNode:
            numeroTentativas = 10

            """
            A mensagem 'root?' ao rendezvous e utilizada para pedir
            pelo endereco do root node
            """
            self.s.sendto('root?', self.enderecoRendezvous)

            # O timer e definido como meio segundo
            self.s.settimeout(0.5)

            # Tenta se comunicar 10 vezes com o root node
            while numeroTentativas > 0:
                try:
                    self.rootAddr, servAddr = self.s.recvfrom(1024)
                    break
                except timeout:
                    if numeroTentativas != 1:
                        self.s.sendto('root?', self.enderecoRendezvous)
                    numeroTentativas -= 1

            """
            Se nao conseguiu se comunicar com o rendezvous em 10 tentativas,
            desiste (retorna False)
            """
            if numeroTentativas == 0:

                # Antes de retornar, volta o socket para o modo sem timer
                self.s.setblocking(1)
                return False

        # Antes de retornar, volta o socket para o modo sem timer
        self.s.setblocking(1)
        return True

    """
    Metodo para visualizar as informacoes basicas do no
    ele deve ser re-escrito para informar o endereco dos nos
    vizinhos na DHT
    """
    def exibeStatus(self):

        if self.meuID != -1:
            print u'Meu ID: ' + repr(self.meuID)
            if self.souRootNode:
                print u'Sou o root node'
            else:
                print u'Não sou o root node'
                print u'Endereco do root node: ' + repr(self.rootAddr)
        else:
            print u'Nó não conectado a rede'

    """
    Quando for necessario avisar o Rendezvous que um nó foi removido da rede
    (retorna True, caso sucesso e False caso nao obtenha resposta do
    rendezvous)
    """
    def avisaRendezvousNoRemovido(self, nodeID):
        numeroTentativas = 10

        """
        A mensagem para informar o rendezvous que um no saiu da rede e
        'nodeOff' + ID_do_no_que_saiu + ID_do_no_que_esta_informando
        """
        self.s.sendto('nodeOff' + repr(nodeID) + '|' + repr(self.meuID),
                      self.enderecoRendezvous)

        # O timer e definido como meio segundo
        self.s.settimeout(0.5)

        """
        Tenta se comunicar com o rendezvous 10 vezes se nao conseguir desiste
        (retornando False)
        """
        while numeroTentativas > 0:
            try:
                msg, servAddr = self.s.recvfrom(1024)

                """
                Resposta do rendezvous caso o no removido for o root node.
                Nesse caso o no sabe que ele e o novo root node a partir de
                agora
                """
                if msg == 'RnodeRemoved':
                    self.souRootNode = True
                    break

                # Resposta do rendezvous se o no removido nao era o root node
                elif msg == 'NnodeRemoved':
                    break
                else:
                    numeroTentativas -= 1
            except timeout:
                if numeroTentativas != 1:
                    self.s.sendto('nodeOff' + repr(nodeID) + '|' +
                                  repr(self.meuID), self.enderecoRendezvous)
                numeroTentativas -= 1

        """
        Se nao conseguiu se comunicar com o rendezvous em 10 tentativas,
        desiste (retorna False)
        """
        if numeroTentativas == 0:

            # Antes de retornar, volta o socket para o modo sem timer
            self.s.setblocking(1)
            return False

        # Antes de retornar, volta o socket para o modo sem timer
        self.s.setblocking(1)
        return True

if __name__ == "__main__":
    no = Node()
    no.conectaRendezvous()
    no.pedeEnderecoRootNode()
    no.exibeStatus()

