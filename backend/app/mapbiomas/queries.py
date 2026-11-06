"""Queries GraphQL de MapBiomas Alerta (ver research.md R4/R5)."""

SIGN_IN_MUTATION = """
mutation SignIn($email: String!, $password: String!) {
  signIn(email: $email, password: $password) { token }
}
"""

CAR_EXISTS_QUERY = """
query CarExists($code: String!) {
  ruralProperty(propertyCode: $code) { propertyCode }
}
"""

RURAL_PROPERTY_QUERY = """
query RuralPropertyCar($code: String!) {
  ruralProperty(propertyCode: $code) {
    propertyCode propertyType carType areaHa stateAcronym geomRuralProperty
    alerts {
      alertCode detectedAt areaHa
      crossedRuralProperties(carCode: $code) { code alertAreaInCar }
      crossedEmbargoesTotal crossedEmbargoesIds crossedEmbargoesList
    }
  }
}
"""

EMBARGO_FIELDS = """carCode embargoedAreasCount embargoedAreas {
    code source processCode areaHa description legislation
    sourceRegisteredAt sourceExpiredAt updatedAt }"""

CAR_EMBARGOES_VIA_ALERTS_QUERY = f"""
query CarEmbargoesViaAlerts($c: [ID!], $code: String) {{
  alerts(propertyCodes: $c, limit: 1) {{
    collection {{ ruralProperties(carCode: $code) {{ {EMBARGO_FIELDS} }} }}
  }}
}}
"""

CAR_EMBARGOES_VIA_POINT_QUERY = f"""
query CarEmbargoesViaPoint($b: BoundingBoxInput) {{
  pointInformation(boundingBox: $b) {{ ruralProperties {{ {EMBARGO_FIELDS} }} }}
}}
"""

# ---- Feature 003: situación de cada alerta (specs/003-car-indicators/research.md R1) ----
ALERT_INDICATORS_QUERY = """
query AlertIndicators($c: [ID!]) {
  alerts(propertyCodes: $c, limit: 200) {
    collection {
      alertCode detectedAt areaHa
      crossedRuralProperties { code alertAreaInCar }
      crossedDeforestationAuthorizationsArea crossedForestManagementsArea
      crossedLegalReservesArea crossedPermanentProtectedAreaTotal
      crossedIndigenousLandsArea
      crossedFederalProtectedAreaIntegralProtectionsArea crossedStateProtectedAreaIntegralProtectionsArea
      crossedMunicipalityProtectedAreaIntegralProtectionsArea
      crossedFederalProtectedAreaSustainableUsesArea crossedStateProtectedAreaSustainableUsesArea
      crossedMunicipalityProtectedAreaSustainableUsesArea
      crossedConservationUnitsList crossedEmbargoesArea actionsList
    }
  }
}
"""

JUDICIAL_ALERTS_QUERY = """
query SuspendedJudicialAlerts($c: String!) { findSuspendedJudicialAlert(carCode: $c) { alertCode } }
"""
