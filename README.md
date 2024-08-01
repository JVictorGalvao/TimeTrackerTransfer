# TimeTrackerTransfer

Esse é um pequeno "projeto" pessoal pra poupar tempo no fim do mês. Basicamente, ele consiste em um *transfer* dos apontamentos de horas do Netproject para o SGI. Para utilizá-lo, basta ter Python instalado e executar o seguinte comando na raíz do projeto:

`$ pip install -r requirements.txt`

Dessa forma, você estará instalando as dependências necessárias para o script ser executado. Após instalar as dependências, será necessário exportar 5 variáveis de ambiente no seu shell: 

* NETPROJECT_USER
* NETPROJECT_PASSWORD
* SGI_USER
* SGI_PASSWORD
* CHROMEDRIVE_VERSION

As primeiras 4 são autoexplicativas, porém a quinta é crucial para o funcionamento do script. O `CHROMEDRIVE_VERSION` depende unicamente da versão do Chrome instalada na sua máquina. Para verificar a versão do seu Chrome, basta abrir o navegador, ir em Mais Opções (3 pontos no canto superior direito) -> Ajuda -> Sobre o Google Chrome. Nesta tela, você verá a versão do seu navegador.

Para versões iguais ou acima da 115, a `CHROMEDRIVE_VERSION` é igual a versão do próprio Chrome. Para versões iguais ou inferiores a 114, você terá que analisar a versão compatível com o seu navegador [aqui](https://developer.chrome.com/docs/chromedriver/downloads/version-selection?hl=pt-br). Sugiro atualizá-lo, dará menos trabalho.

Note que a versão não é apenas '114' ou '115', mas sim '114.0.2563...' então, é necessário passar a versão **completa**, para a variável. Por exemplo, para a versão 127.0.6533.88 (Versão 127),  basta passar exatamente isso (127.0.6533.88) para a `CHROMEDRIVER_VERSION`, que o script funcionará.

Após instalar as dependências e atribuir as variáveis de ambiente, basta executar o script:

`$ python main.py`
