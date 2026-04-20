# HandGestureRPS

Aplicação desktop de reconhecimento de gestos em tempo real utilizando visão computacional. O sistema captura imagens da webcam, identifica a posição das mãos e classifica gestos para simular o jogo pedra, papel e tesoura.

## Sobre o Projeto

O HandGestureRPS é uma aplicação desenvolvida em Python que utiliza OpenCV e MediaPipe para detecção de mãos e classificação de gestos com base em landmarks. A aplicação possui interface gráfica construída com PyQt5, processamento assíncrono com threads e um sistema completo de jogo com estatísticas e configurações persistentes.

## Tecnologias

- Python
- OpenCV
- MediaPipe
- PyQt5
- NumPy

## Principais Funcionalidades

- Captura de vídeo em tempo real via webcam
- Detecção de mãos utilizando MediaPipe
- Classificação de gestos baseada em landmarks (pedra, papel, tesoura)
- Filtro temporal para estabilização da detecção
- Interface gráfica desktop com PyQt5
- Sistema de jogo com regras, placar e feedback ao usuário
- Configurações ajustáveis (confiança de detecção, idioma, som, etc.)
- Persistência de dados (estatísticas e preferências)
- Suporte a múltiplos modos de jogo (estrutura preparada)

## Arquitetura

O sistema é organizado em componentes bem definidos:

- Interface gráfica (PyQt5)
- Detector de gestos em thread separada (QThread)
- Classificador baseado em regras (landmarks da mão)
- Sistema de jogo com controle de estado
- Gerenciamento de configurações e estatísticas

## Como Funciona

A aplicação utiliza a webcam para capturar frames em tempo real. Cada frame é processado pelo MediaPipe para detectar landmarks das mãos. A partir dessas informações, um classificador baseado em regras identifica o gesto com base na posição dos dedos. Um filtro temporal é aplicado para garantir estabilidade na detecção antes de emitir o resultado para a interface.

## Como Executar

### Pré-requisitos

- Python 3.10+
- Webcam

### Instalação

```bash
git clone https://github.com/PedroHenriqueTDS/HandGestureRPS.git
cd HandGestureRPS
pip install -r requirements.txt
