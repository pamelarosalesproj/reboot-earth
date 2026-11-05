// Textos da interface (pt-BR). Centralizados para facilitar traduções futuras.
export const t = {
  appName: 'RebootEarth',
  nav: { login: 'Entrar', register: 'Cadastrar-se', panel: 'Ir para o painel', logout: 'Sair' },

  landing: {
    title: 'Saiba o que os dados ambientais dizem sobre os seus imóveis rurais',
    subtitle:
      'Acompanhe a situação ambiental de cada CAR em um só painel: polígono do imóvel, alertas de desmatamento e embargos.',
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
    ctaTitle: 'Comece agora',
    ctaText: 'O cadastro leva menos de 1 minuto.',
  },

  auth: {
    loginTitle: 'Entrar',
    registerTitle: 'Criar conta',
    registerIntro: 'Depois de criar a conta, você adiciona seus CARs no painel.',
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

  sidebar: { home: 'Início', cars: 'Meus CARs' },

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
