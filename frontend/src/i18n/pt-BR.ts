// Textos da interface (pt-BR). Centralizados para facilitar traduções futuras.
export const t = {
  appName: 'RebootEarth',
  nav: { login: 'Entrar', register: 'Cadastrar-se', panel: 'Ir para o painel', logout: 'Sair', search: 'Consultar CNPJ' },

  landing: {
    title: 'Saiba o que os dados ambientais dizem sobre os seus imóveis rurais',
    subtitle:
      'Produtores acompanham a situação ambiental de cada CAR em um só painel. Compradores consultam o status de um produtor pelo CNPJ, sem cadastro.',
    whatTitle: 'O que você vê por CAR',
    what: [
      { title: 'Polígono do imóvel', text: 'O contorno do imóvel desenhado no mapa, como está registrado no CAR.' },
      {
        title: 'Alertas de desmatamento',
        text: 'Quantos alertas cruzam o imóvel, com data de detecção e área afetada dentro do CAR.',
      },
      {
        title: 'Embargos',
        text: 'Embargos do IBAMA, ICMBio e órgãos estaduais registrados no imóvel e em cada alerta.',
      },
    ],
    howTitle: 'Como funciona',
    how: [
      { title: 'Cadastre-se', text: 'Crie sua conta só com email, CNPJ e senha.' },
      { title: 'Adicione seus CARs', text: 'No painel, informe o código de cada imóvel rural que você quer acompanhar.' },
      { title: 'Veja o painel', text: 'Cada CAR aparece em um cartão com mapa, alertas e embargos.' },
    ],
    sourceTitle: 'De onde vêm os dados',
    sourceText:
      'As informações de polígonos, alertas e embargos vêm do MapBiomas Alerta, sistema que valida e refina alertas de desmatamento em todo o Brasil. A plataforma não altera esses dados: apenas os organiza por imóvel.',
    sourceLink: 'Conheça o MapBiomas Alerta',
    buyerCta: 'É comprador? Consulte o status do seu produtor',
    buyerTitle: 'Para quem compra',
    buyerText:
      'Frigoríficos, tradings, cooperativas e varejistas podem consultar o CNPJ de um produtor sem se cadastrar e ver o nível socioambiental dele, com base nos dados do MapBiomas Alerta.',
    buyerLevels: [
      { level: 'gold', text: 'Sem alertas de desmatamento nem embargos.' },
      { level: 'silver', text: 'Com alertas de desmatamento, ou dados parciais.' },
      { level: 'bronze', text: 'Com embargos registrados.' },
      { level: 'sem_dados', text: 'Sem dados suficientes, ou CNPJ não cadastrado.' },
    ] as const,
    buyerPrivacy: 'A consulta mostra só o resumo do CNPJ: nunca códigos de CAR, mapas ou dados da conta do produtor.',
    ctaTitle: 'Comece agora',
    ctaText: 'O cadastro leva menos de 1 minuto.',
  },

  auth: {
    loginTitle: 'Entrar',
    registerTitle: 'Criar conta',
    registerIntro: 'Depois de criar a conta, você adiciona seus CARs no painel.',
    cnpjPublicNotice:
      'O resumo do seu CNPJ (nível e score) poderá ser consultado publicamente; códigos de CAR e mapas não.',
    email: 'Email',
    password: 'Senha',
    passwordHint: 'Mínimo de 8 caracteres',
    cnpj: 'CNPJ',
    carsHint: 'Formato: UF-0000000-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    submitLogin: 'Entrar',
    submitRegister: 'Criar conta',
    noAccount: 'Ainda não tem conta?',
    hasAccount: 'Já tem conta?',
    emailTaken: 'Este email já está cadastrado.',
    tryLater: 'O MapBiomas Alerta não respondeu. Tente novamente mais tarde.',
    invalidCar: 'Formato de CAR inválido',
    genericError: 'Algo deu errado. Tente novamente.',
  },

  sidebar: { home: 'Início', cars: 'Meus CARs', search: 'Consultar CNPJ' },

  home: {
    greeting: (name: string) => `Olá, ${name}`,
    subtitle: 'Resumo ambiental de todos os seus imóveis rurais, com dados do MapBiomas Alerta.',
    cars: 'CARs cadastrados',
    alerts: 'Alertas de desmatamento',
    embargoes: 'Embargos',
    alertsHint: 'Alertas únicos em todos os seus CARs',
    embargoesHint: 'Embargos únicos (órgão + processo)',
    partial: (n: number) => (n === 1 ? '1 CAR sem dados no momento' : `${n} CARs sem dados no momento`),
    embargoesUnknown: (n: number) =>
      n === 1 ? '1 CAR com embargos não determináveis' : `${n} CARs com embargos não determináveis`,
    addFirst: 'Adicionar meu primeiro CAR',
    seeCars: 'Ver meus CARs →',
    buyerViewTitle: 'Como compradores veem seu CNPJ',
    buyerViewLink: 'Ver ficha pública →',
  },

  panel: {
    alerts: (n: number) => (n === 1 ? '1 alerta' : `${n} alertas`),
    embargoes: (n: number) => (n === 1 ? '1 embargo' : `${n} embargos`),
    embargoesNotDeterminable: 'Não determinável',
    embargoesUnavailable: 'Dados indisponíveis',
    alertsLabel: 'Alertas de desmatamento',
    embargoesLabel: 'Embargos',
    loading: 'Carregando dados do MapBiomas…',
    unavailable: 'Dados indisponíveis no momento.',
    retry: 'Tentar novamente',
    refresh: 'Atualizar',
    stale: 'Dados desatualizados: o MapBiomas não respondeu, mostrando a última consulta.',
    updatedAt: (d: string) => `Atualizado em ${d}`,
    details: 'Ver detalhes',
    remove: 'Remover',
    confirmRemove: 'Remover este CAR?',
    yes: 'Sim, remover',
    no: 'Cancelar',
    addTitle: 'Adicionar CAR',
    add: 'Adicionar CAR',
    adding: 'Verificando…',
    emptyTitle: 'Adicione seu primeiro CAR',
    emptyText:
      'Informe o código do CAR do imóvel rural que você quer acompanhar. Você poderá adicionar outros depois.',
    notInMapBiomas: 'CAR sem registro no MapBiomas Alerta (sem alertas).',
    noPolygon: 'Polígono indisponível',
    area: (ha: number) => `${ha.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} ha`,
  },

  status: {
    title: 'Nível',
    level: { gold: 'Gold', silver: 'Silver', bronze: 'Bronze', sem_dados: 'Sem dados' },
    reason: {
      not_registered: 'CNPJ não cadastrado na plataforma',
      no_properties: 'Nenhuma propriedade informada',
      data_unavailable: 'Dados indisponíveis',
    },
    explain: {
      gold: 'Sem alertas de desmatamento nem embargos nas propriedades informadas.',
      silver: 'Há alertas de desmatamento, ou parte dos dados não pôde ser verificada.',
      bronze: 'Há embargos registrados.',
      sem_dados: 'Não há dados suficientes para avaliar.',
    },
    provisional:
      'Indicador preliminar baseado apenas em alertas e embargos do MapBiomas Alerta; não é o score definitivo.',
    score: {
      em_calculo: 'Score em cálculo',
      nao_calculavel: 'Score não calculável',
      disponivel: (v: number) => `Score: ${v.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}`,
    },
  },

  publicSearch: {
    title: 'Consultar CNPJ',
    subtitle: 'Veja o status socioambiental de um produtor, sem cadastro.',
    label: 'CNPJ do produtor',
    placeholder: '00.000.000/0000-00',
    submit: 'Consultar',
    invalid: 'CNPJ inválido. Confira os 14 dígitos.',
    loading: 'Consultando…',
    rateLimited: (min: number) =>
      `Limite de consultas atingido. Tente novamente em ${min === 1 ? '1 minuto' : `${min} minutos`}.`,
    error: 'Não foi possível consultar agora. Tente novamente.',
    properties: (n: number) =>
      n === 1 ? '1 propriedade informada pelo produtor' : `${n} propriedades informadas pelo produtor`,
    partial: (x: number, y: number) => `Dados parciais: ${x} de ${y} propriedades.`,
    dataAsOf: (d: string) => `Dados de ${d}`,
    stale: 'desatualizado',
    notRegisteredNote:
      'Isso não indica risco nem ausência de risco: apenas que o produtor ainda não está na plataforma.',
  },

  detail: {
    back: '← Voltar',
    alertsTitle: 'Alertas de desmatamento',
    embargoesTitle: 'Embargos do imóvel',
    noAlerts: 'Nenhum alerta.',
    noEmbargoes: 'Nenhum embargo.',
    cols: {
      code: 'Código',
      detected: 'Data de detecção',
      area: 'Área total (ha)',
      areaInCar: 'Área no CAR (ha)',
      embargoes: 'Embargos',
      source: 'Órgão',
      process: 'Nº do processo',
      registered: 'Data de registro',
      descriptions: 'Descrição',
    },
  },
}

export const fmtDate = (iso: string | null) =>
  iso ? new Date(iso.length === 10 ? `${iso}T12:00:00` : iso).toLocaleDateString('pt-BR') : '—'
export const fmtDateTime = (iso: string) => new Date(iso).toLocaleString('pt-BR')
export const fmtNum = (n: number | null) =>
  n == null ? '—' : n.toLocaleString('pt-BR', { maximumFractionDigits: 2 })
