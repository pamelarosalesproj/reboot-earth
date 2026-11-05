# Esquema GraphQL – MapBiomas Alerta

Endpoint: `https://staging.plataforma.alerta.mapbiomas.org/api/v2/graphql`


## Query

- `actionsTypes` → `[ActionResult!]`
  - Returns the list with the actions types present in the platform
- `alert(alertCode: Int!, propertyCode: String)` → `AlertData`
  - Through an alert code you can perform a search for more information through the query alert(alertCode: $alertCode), in this request you will inform the alert code and the API will return the main information. The result can be customized by you, for this example the request will return information such as biomes, cities, crossed properties, sources and the alert geometry.
- `alertDateRange(startDate: BaseDate)` → `AlertRange!`
  - Maximum and minimum publication dates of alerts, being that alert publications are weekly
- `alertStatusByBiomes` → `[MvAlertStatusByBiome!]!`
  - Alert status by biomes
- `alerts(alertCodes: [ID!], propertyCodes: [ID!], page: Int, limit: Int, startDate: BaseDate, endDate: BaseDate, dateType: DateTypes, startSize: Float, endSize: Float, territoryIds: [Int!], territoryCategory: String, statusName: String, sources: [SourceTypes!], intersectWithCar: Boolean, isInEmbargoedAlerta: Boolean, isInEmbargoedRuralProperty: Boolean, isInAuthorizedArea: Boolean, deforestationClasses: [DeforestationTypes!], actionTypesIds: [Int!], boundingBox: [Float!], sortField: AlertSortField, sortDirection: SortDirection)` → `AlertDataCollection!`
  - The query alerts is used to search for alerts published on the platform. It has filters such as: publication date and detection date, size, search area, etc. The result will be a paginated list of alerts.
- `areasOfInterest` → `[MyMap!]`
  - The areas of interest are the way a user monitors a particular area of interest for current and future alerts. To query your areas of interest, use the myMaps() query. The request will return all areas of interest already created by your user.
- `currentlyInPrivacyNotice(destination: PrivacyNoticeEnum)` → `PrivacyNotice!`
  - Returns the privacy notice currently in use on the platform
- `currentlyInTermOfUse(destination: TermOfUseEnum)` → `TermOfUse!`
  - Returns the current terms of use on the platform
- `downloadShapefile(alertCodes: [ID!], propertyCodes: [ID!], startDate: BaseDate, endDate: BaseDate, dateType: DateTypes, startSize: Float, endSize: Float, territoryIds: [Int!], territoryCategory: String, statusName: String, sources: [SourceTypes!], intersectWithCar: Boolean, isInEmbargoedAlerta: Boolean, isInEmbargoedRuralProperty: Boolean, isInAuthorizedArea: Boolean, deforestationClasses: [DeforestationTypes!], actionTypesIds: [Int!], boundingBox: [Float!], sortField: AlertSortField, sortDirection: SortDirection)` → `String!`
  - download_shape
- `findLastUpdateRelatory` → `[RelatoryAlert!]`
- `findSuspendedJudicialAlert(carCode: String!)` → `[AlertData!]`
- `institutionsCsvExport` → `String`
- `lastAlertPublication` → `LastAlertPublication!`
  - Returns the last date when alerts were published on the platform and the number of alerts that were published
- `platformFeatureFlags` → `[PlatformFeatureFlag!]!`
  - Returns the platform feature flags and their respective status (enabled/disabled)
- `pointInformation(boundingBox: BoundingBoxInput)` → `PointInformation!`
  - Returns the information of territories that cross the searched point
- `relatoryAlert(format: RelatoryTypenameTypes, typename: RelatoryFormatTypes)` → `RelatoryAlert`
  - You will need to download all alerts in the desired format (csv/shapefile) and also the type of content of the file (alerts or alerts with crossing with Rural Property)
- `relatoryAttributes` → `[RelatoryTemplate!]`
- `ruralProperty(propertyCode: String)` → `RuralPropertyData`
  - Perform an alert search from a rural property (CAR/SIGEF/SNCI) through the query ruralProperty(carCode: $carCode) . The request requires a Rural Property crossed with alerts in our database and returns a list with all alerts linked to this specific rural property
- `supportCases(page: Int, limit: Int, userOrDescriptionCont: String, supportCaseTypeEq: String, lastStatusEq: Int, isAdminPage: Boolean)` → `SupportCaseCollection!`
  - Returns the support cases of the user that is making the request
- `territoryOptions` → `[TerritoryCategory!]!`
  - You can query all territories of the platform through the query territory_options(category: $category). The request has a parameter for the type of territory (biomes, municipalities, conservation areas, etc) and will return all territories that you can use to perform alert search.
- `usersAndInstitutionsXlsxExport` → `String`
- `usersCsvExport` → `String`
- `version` → `APIVersion!`
  - Show the current version of the API

## Mutation

- `signIn(email: String!, password: String!)` → `Login!`
  - Sign in
- `signOut(sessionToken: String!, signOutOfAllDevices: Boolean)` → `MessageStatus!`
  - Sign out

## Tipos


### APIVersion (OBJECT)

Api version

- `buildDate` → `String!`
- `buildHash` → `String!`
- `rubyVersion` → `String!`
- `version` → `String!`

### Action (OBJECT)

Mapbiomas Alerta Action

- `actionDate` → `BaseDate`
- `actionType` → `String`
- `activities` → `[Activity!]`
- `alertCode` → `String`
- `alertGeometry` → `AlertGeometry`
- `alertGeometryId` → `Int`
- `createdAt` → `BaseDateTime`
- `description` → `String`
- `id` → `Int!`
- `institutionName` → `String`
- `link` → `String`
- `process` → `String`
- `ruralProperty` → `RuralProperty`
- `ruralPropertyId` → `Int`
- `ruralPropertyVersion` → `Int`
- `updatedAt` → `BaseDateTime`
- `user` → `User`
- `userId` → `Int`

### ActionOfBatch (OBJECT)

Mapbiomas Alerta Batch of Actions

- `action` → `Action`
- `actionBatch` → `[ActionsBatch!]`
- `actionId` → `Int`
- `fileData` → `BaseJSON`
- `id` → `ID!`
- `line` → `Int`
- `status` → `ActionsBatchStatus`

### ActionResult (OBJECT)

Alert Action result informations

- `key` → `String`
- `value` → `Int`

### ActionsBatch (OBJECT)

Translation missing: pt-BR.graphql.types.actions_batch.description

- `actionOfBatches` → `[ActionOfBatch!]`
- `createdAt` → `BaseDateTime`
- `generatedActionsCount` → `Int`
- `id` → `ID!`
- `observations` → `String`
- `processedLinesCount` → `Int`
- `status` → `ActionsBatchStatus`
- `user` → `User`
- `xlsxUploaded` → `String`
- `xlsxUploadedFilename` → `String`
- `xlsxUploadedUrl` → `String`

### ActionsBatchStatus (ENUM)

Mapbiomas ActionsBatchStatus

- `Waiting`
- `InProgress`
- `Finished`
- `Error`
- `RemovingActions`
- `ActionsRemoved`
- `ErrorRemovingActions`

### Activity (OBJECT)

Mapbiomas Alerta Activity

- `action` → `Action!`
- `date` → `BaseDate`
- `description` → `String!`
- `id` → `Int!`
- `user` → `User`

### Alert (OBJECT)

Mapbiomas Alerta Alert

- `afterImage` → `PublishedImage`
- `alertCode` → `String!`
- `alertStatus` → `[AlertStatus!]`
- `areaHa` → `Float!`
- `beforeImage` → `PublishedImage`
- `boundingBox` → `[Float!]!`
- `classesLabels` → `BaseJSON`
- `code` → `String!`
- `coordinates` → `LatLng!`
- `detectedAt` → `BaseDate!`
- `imagesLabels` → `BaseJSON`
- `lastAlertStatus` → `AlertStatus`
- `publishedAt` → `BaseDate!`
- `publishedImages` → `[PublishedImage!]`
- `ruralProperties` → `[AlertCAR!]`
- `sources` → `[String!]`
- `warnings` → `BaseJSON`

### AlertActivation (OBJECT)

Mapbiomas Alerta AlertActivation

- `activatedAt` → `BaseDateTime!`
- `alertStatus` → `AlertStatus!`
- `alertStatusId` → `Int!`
- `areaHa` → `Float!`
- `fromToolkit` → `Boolean!`
- `id` → `Int!`
- `images` → `[Image!]!`
- `insertedAt` → `BaseDateTime!`
- `oldId` → `Int!`
- `userEmail` → `String!`
- `userName` → `String!`

### AlertCAR (OBJECT)

Alert car

- `area` → `Float!`
- `code` → `String!`
- `id` → `Int!`
- `intersectionArea` → `Float!`
- `type` → `String!`

### AlertData (OBJECT)

Mapbiomas Data of an Alerta

- `actions` → `[Action!]`
- `actionsList` → `BaseJSON`
- `actionsTypeIds` → `[Int!]`
- `alertCode` → `Int`
- `alertGeometry` → `AlertGeometry`
- `alertGeometryId` → `Int`
- `alertImageBbox` → `String`
- `alertIntersections` → `[AlertIntersection!]`
- `areaHa` → `Float`
- `bbox` → `String`
- `boundingBox` → `BoundingBox`
- `categories` → `[String!]`
- `classesLabels` → `[ClassLabel!]`
- `codes` → `[Int!]`
- `coordenates` → `LatLng`
- `crossedBiomes` → `[String!]`
- `crossedBiomesArea` → `Float`
- `crossedBiomesIds` → `[Int!]`
- `crossedBiomesList` → `BaseJSON`
- `crossedBiosphereReserves` → `[String!]`
- `crossedBiosphereReservesArea` → `Float`
- `crossedBiosphereReservesIds` → `[Int!]`
- `crossedCities` → `[String!]`
- `crossedCitiesArea` → `Float`
- `crossedCitiesIds` → `[Int!]`
- `crossedCitiesList` → `BaseJSON`
- `crossedConservationUnits` → `[String!]`
- `crossedConservationUnitsArea` → `Float`
- `crossedConservationUnitsIds` → `[Int!]`
- `crossedConservationUnitsList` → `BaseJSON`
- `crossedDeforestationAuthorizationRuralPropertiesArea` → `Float`
- `crossedDeforestationAuthorizationRuralPropertiesList` → `BaseJSON`
- `crossedDeforestationAuthorizationsActivities` → `[String!]`
- `crossedDeforestationAuthorizationsArea` → `Float`
- `crossedDeforestationAuthorizationsAreasIds` → `[Int!]`
- `crossedDeforestationAuthorizationsCategories` → `[String!]`
- `crossedDeforestationAuthorizationsList` → `BaseJSON`
- `crossedEmbargoesArea` → `Float`
- `crossedEmbargoesIds` → `[Int!]`
- `crossedEmbargoesList` → `BaseJSON`
- `crossedEmbargoesRuralPropertiesArea` → `Float`
- `crossedEmbargoesRuralPropertiesIds` → `[Int!]`
- `crossedEmbargoesRuralPropertiesList` → `BaseJSON`
- `crossedEmbargoesRuralPropertiesTotal` → `Int`
- `crossedEmbargoesTotal` → `Int`
- `crossedFederalProtectedAreaIntegralProtections` → `[String!]`
- `crossedFederalProtectedAreaIntegralProtectionsArea` → `Float`
- `crossedFederalProtectedAreaSustainableUses` → `[String!]`
- `crossedFederalProtectedAreaSustainableUsesArea` → `Float`
- `crossedForestManagementRuralPropertiesArea` → `Float`
- `crossedForestManagementRuralPropertiesList` → `BaseJSON`
- `crossedForestManagementsActivities` → `[String!]`
- `crossedForestManagementsArea` → `Float`
- `crossedForestManagementsCategories` → `[String!]`
- `crossedForestManagementsList` → `BaseJSON`
- `crossedGeoparks` → `[String!]`
- `crossedGeoparksArea` → `Float`
- `crossedGeoparksIds` → `[Int!]`
- `crossedIndigenousLands` → `[String!]`
- `crossedIndigenousLandsArea` → `Float`
- `crossedIndigenousLandsIds` → `[Int!]`
- `crossedIndigenousLandsList` → `BaseJSON`
- `crossedLegalReserveRuralPropertiesArea` → `Float`
- `crossedLegalReserveRuralPropertiesList` → `BaseJSON`
- `crossedLegalReserveRuralPropertiesTotal` → `Int`
- `crossedLegalReserves(carId: Int)` → `[CrossedLegalReserve!]`
- `crossedLegalReservesArea` → `Float`
- `crossedLegalReservesList` → `BaseJSON`
- `crossedLegalReservesTotal` → `Int`
- `crossedMunicipalityProtectedAreaIntegralProtections` → `[String!]`
- `crossedMunicipalityProtectedAreaIntegralProtectionsArea` → `Float`
- `crossedMunicipalityProtectedAreaSustainableUses` → `[String!]`
- `crossedMunicipalityProtectedAreaSustainableUsesArea` → `Float`
- `crossedPermanentProtectedArea` → `Float`
- `crossedPermanentProtectedAreaList` → `BaseJSON`
- `crossedPermanentProtectedAreaTotal` → `Int`
- `crossedPermanentProtectedAreas(carId: Int)` → `[CrossedPermanentProtectedArea!]`
- `crossedPermanentProtectedList` → `BaseJSON`
  - Crossed permanent protected list
- `crossedPermanentProtectedRuralPropertiesArea` → `Float`
- `crossedPermanentProtectedRuralPropertiesList` → `BaseJSON`
- `crossedPermanentProtectedRuralPropertiesTotal` → `Int`
- `crossedQuilombos` → `[String!]`
- `crossedQuilombosArea` → `Float`
- `crossedQuilombosIds` → `[Int!]`
- `crossedQuilombosList` → `BaseJSON`
- `crossedRiverSourcesArea` → `Float`
- `crossedRuralProperties(ruralPropertyCode: String, carCode: String, carId: Int)` → `[AlertRuralProperty!]`
- `crossedSettlements` → `[String!]`
- `crossedSettlementsArea` → `Float`
- `crossedSettlementsIds` → `[Int!]`
- `crossedSettlementsList` → `BaseJSON`
- `crossedSettlementsRuralPropertiesArea` → `Float`
- `crossedSettlementsRuralPropertiesList` → `BaseJSON`
- `crossedSettlementsRuralPropertiesTotal` → `Int`
- `crossedSpecialTerritories` → `[String!]`
- `crossedSpecialTerritoriesArea` → `Float`
- `crossedSpecialTerritoriesIds` → `[Int!]`
- `crossedSpecialTerritoryAmacroArea` → `Float`
- `crossedSpecialTerritoryAmazoniaLegalArea` → `Float`
- `crossedSpecialTerritoryLeiDaMataAtlanticaArea` → `Float`
- `crossedSpecialTerritoryMatopibaArea` → `Float`
- `crossedSpecialTerritorySemiaridoArea` → `Float`
- `crossedStateProtectedAreaIntegralProtections` → `[String!]`
- `crossedStateProtectedAreaIntegralProtectionsArea` → `Float`
- `crossedStateProtectedAreaSustainableUses` → `[String!]`
- `crossedStateProtectedAreaSustainableUsesArea` → `Float`
- `crossedStates` → `[String!]`
- `crossedStatesArea` → `Float`
- `crossedStatesIds` → `[Int!]`
- `crossedStatesList` → `BaseJSON`
- `crossedTerritoriesIds` → `[Int!]`
- `crossedWatersheds` → `[String!]`
- `crossedWatershedsArea` → `Float`
- `crossedWatershedsIds` → `[Int!]`
- `crossedWatershedsList` → `BaseJSON`
- `datum` → `String`
- `deforestationClasses` → `[String!]`
- `deforestationSpeed` → `String`
- `detectedAt` → `BaseDate`
- `embargoedAreasIds` → `[Int!]`
  - Embargoed areas ids
- `exclusionCategories` → `[String!]`
- `geometryWkt` → `String`
- `id` → `Int!`
- `imageAcquiredAfterAt` → `BaseDate`
- `imageAcquiredAfterList` → `BaseJSON`
- `imageAcquiredBeboreList` → `BaseJSON`
- `imageAcquiredBeforeAt` → `BaseDate`
- `imageAcquiredBeforeList` → `BaseJSON`
- `imageContext` → `ImageContext`
- `imagesLabels` → `[ImageLabel!]`
- `legendLclu` → `[LegendPoint!]`
- `publicationCycles` → `Int`
- `publicationCyclesList` → `BaseJSON`
- `publishedAt` → `BaseDate`
- `publishedImages(ruralPropertyCode: String, carCode: String, carId: Int)` → `[PublishedImage!]`
- `republished` → `Boolean`
- `ruralProperties(ruralPropertyCode: String, carCode: String, carId: Int)` → `[RuralProperty!]`
- `ruralPropertiesCodes` → `[String!]`
- `ruralPropertiesList` → `BaseJSON`
- `ruralPropertiesTotal` → `Int`
- `sources` → `[String!]`
- `statusAt` → `BaseDate`
- `statusName` → `String`
- `supportCaseAuthorizations(ruralPropertyCode: String, carCode: String, carId: Int, supportCaseType: SupportCaseTypes)` → `[SupportCase!]`
- `supportCases(ruralPropertyCode: String, carCode: String, carId: Int)` → `[SupportCase!]`
- `supportCasesIds` → `[Int!]`
- `warnings` → `WarningLabel`

### AlertDataCollection (OBJECT)

Alert query result

- `collection` → `[AlertData!]!`
  - A collection of paginated AlertDataCollection
- `metadata` → `CollectionMetadata!`
  - Pagination Metadata for navigating the Pagination
- `rankingByBiome` → `[AlertRankingByBiome!]`
- `rankingByCity` → `[AlertRankingByCity!]`
- `rankingByState` → `[AlertRankingByState!]`
- `summary` → `QuerySummary`

### AlertGeometry (OBJECT)

Mapbiomas Alerta AlertGeometry

- `afterDeforestationSimplifiedImage` → `String`
- `alertCodeOld` → `Int`
- `alertGeometriesRuralPropertiesSimplifiedPoints` → `[AlertGeometryRuralPropertySimplifiedPoint!]`
- `alertGeometriesSimplifiedPoints` → `[AlertGeometrySimplifiedPoint!]`
- `alertImageBbox` → `BoundingBox`
- `alertStatus` → `[AlertStatus!]`
- `areaHa` → `Float`
- `authorizedAreas` → `[DeforestationAuthorization!]`
- `authorizedAreasArea` → `Float`
- `bbox` → `BaseJSON`
- `changes` → `BaseJSON`
- `changesLandsatMosaicRgb` → `BaseJSON!`
- `changesPlanetMosaic` → `BaseJSON!`
- `changesUsageAndCoverageLandsat` → `BaseJSON!`
- `changesUsageAndCoverageSentinel` → `BaseJSON!`
- `code` → `ID!`
- `conservationUnits` → `[Territory!]`
- `conservationUnitsArea` → `Float`
- `deforestationAuthorizations` → `[DeforestationAuthorization!]`
- `forestManagements` → `[DeforestationAuthorization!]`
- `forestManagementsArea` → `Float`
- `imageGridMeasurements` → `[BaseJSON!]`
- `indigenousLands` → `[Territory!]`
- `indigenousLandsArea` → `Float`
- `layerImage` → `String`
- `legalReserves` → `[LegalReserve!]`
- `legalReservesArea` → `Float`
- `permanentProtectedAreas` → `[PermanentProtectedArea!]`
- `permanentProtectedAreasArea` → `Float`
- `refined` → `Boolean`
- `relatedAlert` → `AlertData`
- `riverSources` → `[RiverSource!]`
- `riverSourcesArea` → `Float`
- `ruralProperties` → `[RuralProperty!]`
- `ruralPropertySimplifiedPoints` → `[AlertGeometryRuralPropertySimplifiedPoint!]`
- `settlements` → `[Territory!]`
- `settlementsArea` → `Float`
- `simplifiedPoints` → `[AlertGeometrySimplifiedPoint!]`
- `territories` → `[Territory!]`

### AlertGeometryRuralPropertySimplifiedPoint (OBJECT)

Mapbiomas Alerta AlertGeometryRuralPropertySimplifiedPoint

- `alertGeometry` → `AlertGeometry`
- `id` → `Int!`
- `number` → `Int`
- `ruralProperty` → `RuralProperty`
- `ruralPropertyId` → `Int`
- `xCoord` → `String`
- `yCoord` → `String`

### AlertGeometrySimplifiedPoint (OBJECT)

Mapbiomas Alerta AlertGeometrySimplifiedPoint

- `alertGeometry` → `AlertGeometry`
- `id` → `Int!`
- `number` → `Int`
- `xCoord` → `String`
- `yCoord` → `String`

### AlertIntersection (OBJECT)

Mapbiomas Alerta Crossing Territory

- `category` → `String`
- `codes` → `[Int!]`
- `name` → `String`
- `names` → `[String!]`
- `total` → `Int`
- `totalAreaHa` → `Float`
- `type` → `source_key`
- `units` → `[AlertIntersectionUnit!]`

### AlertIntersectionUnit (OBJECT)

Mapbiomas Alerta Crossing Territory Unit

- `areaHa` → `Float`
- `code` → `Int`
- `crossAreaHa` → `Float`
- `name` → `String`
- `version` → `Int`

### AlertNotification (OBJECT)

Alert Notification

- `alert` → `Alert!`
- `id` → `Int!`
- `myMapTerritory` → `MyMapTerritory!`
- `seen` → `Boolean`
- `user` → `User`

### AlertRange (OBJECT)

Alert Range informations

- `maxDetectedAt` → `BaseDate`
- `maxPublishedAt` → `BaseDate`
- `minDetectedAt` → `BaseDate`
- `minPublishedAt` → `BaseDate`

### AlertRankingByBiome (OBJECT)

Alert query ranking by biome

- `alertsTotal` → `Int!`
- `area2018` → `Float!`
- `area2019` → `Float!`
- `area2020` → `Float!`
- `area2021` → `Float!`
- `area2022` → `Float!`
- `area2023` → `Float!`
- `area2024` → `Float!`
- `area2025` → `Float!`
- `area2026` → `Float!`
- `areaTotal` → `Float!`
- `biome` → `String!`

### AlertRankingByCity (OBJECT)

Alert query ranking by city

- `alertsTotal` → `Int!`
- `area2018` → `Float!`
- `area2019` → `Float!`
- `area2020` → `Float!`
- `area2021` → `Float!`
- `area2022` → `Float!`
- `area2023` → `Float!`
- `area2024` → `Float!`
- `area2025` → `Float!`
- `area2026` → `Float!`
- `areaTotal` → `Float!`
- `city` → `String!`

### AlertRankingByState (OBJECT)

Alert query ranking by state

- `alertsTotal` → `Int!`
- `area2018` → `Float!`
- `area2019` → `Float!`
- `area2020` → `Float!`
- `area2021` → `Float!`
- `area2022` → `Float!`
- `area2023` → `Float!`
- `area2024` → `Float!`
- `area2025` → `Float!`
- `area2026` → `Float!`
- `areaTotal` → `Float!`
- `state` → `String!`

### AlertRuralProperty (OBJECT)

Mapbiomas Alerta RuralProperty

- `afterDeforestationSimplifiedImage` → `String!`
- `alertAreaInCar` → `Float`
- `alertGeometryCode` → `String`
- `alertInPropertyImage` → `String!`
- `areaHa` → `Float`
- `code` → `String`
- `id` → `Int`
- `insertedAt` → `BaseDateTime`
- `layerImage` → `String!`
- `propertyInStateImage` → `String!`
- `type` → `String`
- `updatedAt` → `BaseDate`
- `version` → `Int`

### AlertSortField (ENUM)

Alert sort field type

- `ALERT_CODE`
- `AREA_HA`
- `DETECTED_AT`
- `STATE`
- `CITY`

### AlertStatus (OBJECT)

Mapbiomas Alerta AlertStatus

- `alert` → `Alert`
- `alertActivations` → `[AlertActivation!]`
- `alertGeometry` → `AlertGeometry`
- `cycle` → `Int`
- `dashboardUserId` → `Int`
- `id` → `Int!`
- `images` → `[Image!]`
- `insertedAt` → `BaseDateTime`
- `progressId` → `Int`
- `publishedAt` → `BaseDateTime`
- `rejectedReasonId` → `Int`
- `status` → `String`
- `userId` → `Int`

### BaseDate (SCALAR)

Data no formato IS8601 (YYYY-MM-DD)


### BaseDateTime (SCALAR)

Datetime in UTC ISO8601 format (yyyy-mm-ddThh:mm:ss)


### BaseJSON (SCALAR)

Base json


### Boolean (SCALAR)

Represents `true` or `false` values.


### BoundingBox (OBJECT)

Bounding box

- `neLat` → `Float`
  - North West latitude
- `neLng` → `Float`
  - North West longitude
- `simplified` → `[Float!]`
- `swLat` → `Float!`
  - South West latitude
- `swLng` → `Float!`
  - South West longitude

### BoundingBoxInput (INPUT_OBJECT)

Bounding box input

- `swLat`: `Float!`
- `swLng`: `Float!`
- `neLat`: `Float!`
- `neLng`: `Float!`

### ClassLabel (OBJECT)

Class label

- `colors` → `[String!]!`
- `colorsWithLabels` → `BaseJSON!`
- `name` → `String!`

### CollectionMetadata (OBJECT)

Type for CollectionMetadataType

- `currentPage` → `Int!`
  - Current Page of loaded data
- `limitValue` → `Int!`
  - The number of items per page
- `totalCount` → `Int!`
  - The total number of items to be paginated
- `totalPages` → `Int!`
  - The total number of pages in the pagination

### CrossedLegalReserve (OBJECT)

Crossed legal reserve

- `legalReserveId` → `Int`
- `legalReserveVersion` → `Int`
- `ruralPropertyId` → `Int`
- `totalAreaHa` → `Float`

### CrossedPermanentProtectedArea (OBJECT)

Crossed permanent protected area

- `permanentProtectedAreaId` → `Int`
- `permanentProtectedAreaVersion` → `Int`
- `ruralPropertyId` → `Int`
- `totalAreaHa` → `Float`

### DateTypes (ENUM)

Date types

- `DetectedAt`
- `PublishedAt`

### DeforestationAuthorization (OBJECT)

Deforestation authorization

- `activity` → `String`
- `areaHa` → `Float`
- `category` → `String`
- `endedAt` → `BaseDate`
- `id` → `Int!`
- `insertedAt` → `BaseDateTime`
- `source` → `String`
- `sourceId` → `String`
- `startedAt` → `BaseDate`
- `updatedAt` → `BaseDateTime`
- `version` → `Int!`

### DeforestationTypes (ENUM)

Deforestation types

- `All`
- `Agriculture`
- `Aquaculture`
- `IlegalMining`
- `Mining`
- `NaturalCause`
- `Others`
- `RenewableEnergyProject`
- `ReservoirOrDam`
- `Roads`
- `UrbanExpansion`

### Domain (OBJECT)

Mapbiomas Alerta Domain

- `id` → `Int`
- `institutionId` → `Institution!`
- `name` → `String!`

### EmbargoedArea (OBJECT)

Mapbiomas Alerta EmbargoedArea

- `areaHa` → `Float`
- `code` → `ID!`
- `description` → `String`
- `insertedAt` → `BaseDateTime`
- `legislation` → `String`
- `processCode` → `String`
- `source` → `String`
- `sourceExpiredAt` → `BaseDate`
- `sourceId` → `String`
- `sourceRegisteredAt` → `BaseDate`
- `updatedAt` → `BaseDateTime`
- `version` → `Int`

### Float (SCALAR)

Represents signed double-precision fractional values as specified by [IEEE 754](https://en.wikipedia.org/wiki/IEEE_floating_point).


### ID (SCALAR)

Represents a unique identifier that is Base64 obfuscated. It is often used to refetch an object or as key for a cache. The ID type appears in a JSON response as a String; however, it is not intended to be human-readable. When expected as an input type, any string (such as `"VXNlci0xMA=="`) or integer (such as `4`) input value will be accepted as an ID.


### Image (OBJECT)

Mapbiomas Alerta Image

- `acquiredAt` → `BaseDateTime!`
- `alertActivation` → `AlertActivation!`
- `alertActivationId` → `Int!`
- `constellation` → `String!`
- `dbId` → `Int!`
- `fromGee` → `Boolean!`
- `gcsExists` → `Boolean!`
- `gcsUrl` → `String!`
- `geeExists` → `Boolean!`
- `id` → `Int!`
- `name` → `String!`
- `product` → `String!`
- `reference` → `String!`

### ImageContext (OBJECT)

Mapbiomas Alerta ImageContext

- `imageAllContext` → `String!`
- `imageStateContext` → `String`

### ImageLabel (OBJECT)

Image label

- `name` → `String!`
- `thumbnailUrl` → `String!`

### Institution (OBJECT)

Mapbiomas Alerta Institution

- `abbreviation` → `String`
- `domains` → `[Domain!]`
- `id` → `Int!`
- `logoContent` → `String`
- `logoUrl` → `String`
- `name` → `String`
- `reportStructureSnapshot` → `BaseJSON`
- `status` → `Int`
- `users` → `[User!]`

### Int (SCALAR)

Represents non-fractional signed whole numeric values. Int can represent values between -(2^31) and 2^31 - 1.


### LastAlertPublication (OBJECT)

Translation missing: pt-BR.graphql.types.last_alert_publication.description

- `publicationRange` → `[BaseDateTime!]!`
- `publishedAt` → `BaseDateTime!`
- `total` → `Int!`

### LatLng (OBJECT)

Lat lng

- `latitude` → `Float`
- `longitude` → `Float`

### LegalReserve (OBJECT)

Mapbiomas Alerta LegalReserve

- `areaHa` → `Int`
- `carCode` → `String`
- `id` → `Int!`
- `insertedAt` → `BaseDateTime`
- `ruralProperty` → `[RuralProperty!]`
- `ruralPropertyId` → `String`
- `stateAcronym` → `String`
- `updatedAt` → `BaseDateTime`
- `version` → `Int`

### LegendPoint (OBJECT)

Mapbiomas Alerta LegendPoint

- `children` → `[LegendPoint]`
- `color` → `String`
- `key` → `String!`
- `name` → `BaseJSON`
- `order` → `Int`

### Login (OBJECT)

Login

- `apiToken` → `String`
- `token` → `String!`

### MessageStatus (OBJECT)

Message status

- `message` → `String!`
  - Message returned
- `status` → `Boolean!`
  - Boolean Status

### MvAlertStatusByBiome (OBJECT)

Mapbiomas Alerts Status by Biomes

- `biome` → `String`
- `total` → `Int`
- `totalNotprocessed` → `Int`
- `totalProcessed` → `Int`
- `yearMonth` → `String`

### MvPublishedAlert (OBJECT)

Mapbiomas Alerta MvPublishedAlert

- `actions` → `[Action!]`
- `actionsTypeIds` → `[Int!]`
- `alertCode` → `Int`
- `alertGeometry` → `AlertGeometry`
- `alertGeometryId` → `Int`
- `areaHa` → `Float`
- `bbox` → `String`
- `biomes` → `[BaseJSON!]`
- `carCodes` → `[String!]`
- `categories` → `String`
- `cities` → `[BaseJSON!]`
- `classesLabels` → `BaseJSON`
- `crossedConservationUnitsArea` → `Float`
- `crossedDeforestationAuthorizationIds` → `[Int!]`
- `crossedDeforestationAuthorizationsArea` → `Float`
- `crossedEmbargoesRuralPropertiesArea` → `Float`
- `crossedEmbargoesRuralPropertiesTotal` → `Int`
- `crossedForestManagementsArea` → `Float`
- `crossedIndigenousLands` → `[BaseJSON!]`
- `crossedIndigenousLandsArea` → `Float`
- `crossedLegalReserveRuralPropertiesList(carId: Int)` → `BaseJSON`
- `crossedLegalReservesRuralPropertiesArea` → `Float`
- `crossedPermanentProtectedAreaRuralPropertiesList(carId: Int)` → `BaseJSON`
- `crossedPermanentProtectedRuralPropertiesArea` → `Float`
- `crossedRuralProperties(carId: Int)` → `[RAlertGeometryRuralProperty!]`
- `crossedSettlementArea` → `Int`
- `crossedSettlements` → `[BaseJSON!]`
- `crossedSettlementsRuralPropertiesList(carId: Int)` → `BaseJSON`
- `datum` → `String`
- `deforestationClasses` → `String`
- `deforestationSpeed` → `Int`
- `detectedAt` → `BaseDate`
- `embargoedAreas` → `[EmbargoedArea!]`
- `embargoedAreasIds` → `[Int!]`
- `embargoesCount` → `Int`
- `exclusionCategories` → `String`
- `id` → `Int!`
- `imageAcquiredAfterAt` → `BaseDate`
- `imageAcquiredBeforeAt` → `BaseDate`
- `imagesLabels` → `BaseJSON`
- `publishedAt` → `BaseDate`
- `publishedImages(carId: Int)` → `[PublishedImage!]`
- `riverSourcesCount` → `Int`
- `ruralProperties(carId: Int)` → `[RuralProperty!]`
- `ruralPropertiesCarCodesOverLimit` → `String`
- `ruralPropertiesCodes` → `String`
- `ruralPropertiesInfoOverLimit` → `[BaseJSON!]`
- `ruralPropertiesJson` → `[BaseJSON!]`
- `ruralPropertiesList` → `[BaseJSON!]`
- `ruralPropertiesTotal` → `Int`
- `ruralPropertiesTotalOverLimit` → `Int`
- `sources` → `[String!]`
- `states` → `[BaseJSON!]`
- `status` → `String`
- `statusAt` → `BaseDate`
- `statusName` → `String`
- `supportCases(carId: Int, carCode: Int)` → `[SupportCase!]`
- `territories` → `[Territory!]`
- `territoriesIds` → `[Int!]`
- `warnings` → `BaseJSON`

### MyMap (OBJECT)

Translation missing: pt-BR.graphql.types.my_map.description

- `alertNotifications` → `[AlertNotification!]`
- `alertNotificationsCount` → `Int`
- `id` → `Int!`
- `name` → `String`
- `territories` → `[Territory!]`
- `user` → `User`

### MyMapTerritory (OBJECT)

Mapbiomas Alerta MyMapTerritory

- `id` → `Int!`
- `myMap` → `MyMap`
- `territory` → `Territory`

### PermanentProtectedArea (OBJECT)

Mapbiomas Alerta PermanentProtectedArea

- `areaHa` → `Float`
- `carCode` → `String`
- `id` → `Int!`
- `insertedAt` → `BaseDateTime`
- `ruralProperty` → `[RuralProperty!]`
- `ruralPropertyId` → `String`
- `stateAcronym` → `String`
- `updatedAt` → `BaseDateTime`
- `version` → `Int`

### PlatformFeatureFlag (OBJECT)

Platform feature flag configuration

- `category` → `String`
- `enabled` → `Boolean!`
- `key` → `String!`

### PointHistoryCoverage (OBJECT)

Mapbiomas Alerta RiverSource

- `history` → `BaseJSON`
- `labels` → `[PointHistoryCoverageLabel!]`

### PointHistoryCoverageLabel (OBJECT)

Mapbiomas Alerta RiverSource

- `classification` → `Int`
- `color` → `String`
- `label` → `String`
- `linguage` → `String`

### PointInformation (OBJECT)

Point information

- `alerts` → `[MvPublishedAlert!]!`
  - Alerts
- `boundingBox` → `[Float!]`
  - Bounding Box
- `historyCoverage` → `PointHistoryCoverage!`
  - Coverage
- `ruralProperties` → `[RuralProperty!]!`
  - RuralProperties
- `territories` → `[Territory!]!`
  - Territories

### PrivacyNotice (OBJECT)

Mapbiomas PrivacyNotice

- `destination` → `PrivacyNoticeEnum!`
- `englishContent` → `String`
- `id` → `Int!`
- `indonesianContent` → `String`
- `portugueseContent` → `String`
- `status` → `Int`
- `version` → `Int`

### PrivacyNoticeEnum (ENUM)

Privacy notice enum

- `Main`
- `AuthorizationRequest`

### PublishedImage (OBJECT)

Mapbiomas Alerta PublishedImage

- `acquiredAt` → `BaseDateTime`
- `alert` → `Alert!`
- `constellation` → `String`
- `fid` → `Int!`
- `location` → `String`
- `reference` → `String`
- `satellite` → `String`
- `url` → `String`
- `urlMedium` → `String`

### QueryStatisticByDate (OBJECT)

Alert query statistics by date

- `date` → `BaseDate!`
- `value` → `Float!`

### QueryStatisticByYear (OBJECT)

Alert query statistics by year

- `value` → `Float!`
- `year` → `Int!`

### QuerySummary (OBJECT)

Alert query summary informations

- `actionsCount` → `Int!`
- `alertsByMonth` → `[QueryStatisticByDate!]!`
- `alertsByYear` → `[QueryStatisticByYear!]!`
- `area` → `Float!`
- `authorizedAreasCount` → `Int!`
- `averageDeforestationSpeed` → `Float!`
- `biggestAlert` → `AlertData`
- `biggestAlertArea` → `Float`
- `biggestDeforestationSpeed` → `Float`
- `biggestDeforestationSpeedAlert` → `AlertData`
- `boundingBox` → `BoundingBox`
- `conservationUnitsCount` → `Int!`
- `deforestationAreaByMonth` → `[QueryStatisticByDate!]!`
- `deforestationAreaByYear` → `[QueryStatisticByYear!]!`
- `embargoesCount` → `Int!`
- `forestManagementsCount` → `Int!`
- `indigenousLandCount` → `Int!`
- `legalReservesCount` → `Int!`
- `lowestAlert` → `AlertData`
- `lowestAlertArea` → `Float`
- `lowestDeforestationSpeed` → `Float`
- `lowestDeforestationSpeedAlert` → `AlertData`
- `permanentProtectedAreasCount` → `Int!`
- `riverSourcesCount` → `Int!`
- `ruralPropertiesCount` → `Int!`
- `settlementsCount` → `Int!`
- `total` → `Int!`

### RAlertGeometryRuralProperty (OBJECT)

Mapbiomas Alerta RAlertGeometryRuralProperty

- `afterDeforestationSimplifiedImage` → `String`
- `alertAreaInCar` → `Float`
- `alertGeometry` → `AlertGeometry!`
- `alertGeometryId` → `Int!`
- `alertInPropertyImage` → `String!`
- `layerImage` → `String`
- `propertyInStateImage` → `String!`
- `ruralPropertyId` → `Int!`
- `ruralPropertyVersion` → `Int!`

### RelatoryAlert (OBJECT)

Alert report

- `fileUrl` → `String`
- `format` → `String`
- `lastUpdate` → `BaseDate`
- `md5` → `String`
- `relatoryMetadatum` → `RelatoryMetadatum`
- `templateVersion` → `Int`
- `typename` → `String`

### RelatoryColumn (OBJECT)

Alert Relatory Column

- `description` → `String`
- `enabled` → `Boolean!`
  - Enabled
- `id` → `Int!`
  - Id
- `name` → `String`
- `typename` → `String`

### RelatoryFormatTypes (ENUM)

Relatory format types

- `Alerts`
- `AlertsCars`

### RelatoryMetadatum (OBJECT)

Alert Relatory Metadatum

- `relatoryColumns` → `[RelatoryColumn!]`
- `relatorySources` → `[RelatorySource!]`

### RelatorySource (OBJECT)

Alert Relatory Source

- `description` → `String`
- `lastUpdate` → `BaseDate`
- `name` → `String`

### RelatoryTemplate (OBJECT)

Alert Relatory Template

- `enabled` → `Boolean!`
  - Enabled
- `format` → `String`
- `id` → `Int!`
  - Id
- `relatoryColumnTemplates(includeDisabled: Boolean)` → `[RelatoryColumn!]`
  - Relatory column templates
- `typename` → `String`
- `version` → `Int`

### RelatoryTypenameTypes (ENUM)

Relatory typename types

- `Csv`
- `Shape`

### RiverSource (OBJECT)

Mapbiomas Alerta RiverSource

- `carCode` → `String`
- `id` → `Int!`
- `insertedAt` → `BaseDateTime`
- `ruralProperty` → `[RuralProperty!]`
- `ruralPropertyId` → `Int`
- `stateAcronym` → `String`
- `updatedAt` → `BaseDateTime`
- `version` → `Int`

### RuralProperty (OBJECT)

Mapbiomas Alerta RuralProperty

- `alertGeometries` → `[AlertGeometry!]`
- `areaHa` → `Float`
- `carCode` → `String`
- `carModule` → `Float`
- `carType` → `String`
- `embargoedAreas` → `[EmbargoedArea!]`
- `embargoedAreasCount` → `Int`
- `insertedAt` → `BaseDateTime`
- `rAlertGeometriesRuralProperties` → `[RAlertGeometryRuralProperty!]`
  - R alert geometries rural properties
- `relatedAlerts` → `[AlertData!]`
- `stateAcronym` → `String`
- `version` → `Int`

### RuralPropertyData (OBJECT)

Mapbiomas Alerta RuralProperty Data

- `alerts` → `[AlertData!]`
- `areaHa` → `Float`
- `boundingBox` → `[Float!]`
- `carType` → `String`
- `carUpdatedAt` → `BaseDate`
- `enabled` → `Boolean`
- `geomRuralProperty` → `String`
- `imageContext` → `ImageContext`
- `insertedAt` → `BaseDateTime`
- `propertyCode` → `String`
- `propertyType` → `String`
- `state` → `String`
- `stateAcronym` → `String`
- `version` → `Int`

### SortDirection (ENUM)

Sort direction type

- `ASC`
- `DESC`

### SourceTypes (ENUM)

Source types

- `All`
- `DeterbAmazonia`
- `DeterCerrado`
- `Glad`
- `IefMg`
- `InemaBa`
- `ProdesAmz`
- `ProdesCerr`
- `ProdesMataAtlantica`
- `ProdesPampa`
- `ProdesPantanal`
- `Sad`
- `SadCaatinga`
- `SadCerrado`
- `SadMataAtlantica`
- `SadPampa`
- `SadPantanal`
- `SipamSar`
- `Siradx`
- `SosInpe`

### String (SCALAR)

Represents textual data as UTF-8 character sequences. This type is most often used by GraphQL to represent free-form human-readable text.


### SupportCase (OBJECT)

Mapbiomas SupportCase

- `accessIp` → `String`
- `alertCode` → `String`
- `authorizedAreaHa` → `Float`
- `authorizingAgency` → `String`
- `carCode` → `String`
- `carId` → `String`
- `code` → `ID!`
- `createdAt` → `String!`
- `description` → `String`
- `documentIssueDate` → `BaseDate`
- `expirationDate` → `BaseDate`
- `lat` → `String`
- `lng` → `String`
- `mvPublishedAlert` → `MvPublishedAlert`
- `ownerAuthorizedPublication` → `Boolean`
- `processNumber` → `String`
- `propertyAreaHa` → `Float`
- `propertyName` → `String`
- `propertyOwnersName` → `String`
- `subject` → `String`
- `supportCaseFiles` → `[SupportCaseFile!]`
- `supportCaseFilesCount` → `Int!`
- `supportCaseMessages` → `[SupportCaseMessage!]`
- `supportCaseStatus` → `[SupportCaseStatus!]`
- `supportCaseStatusCount` → `Int!`
- `supportCaseType` → `String`
- `termsOfUseId` → `String`
- `userEmail` → `String`
- `userIsOwner` → `Boolean`
- `userName` → `String`

### SupportCaseCollection (OBJECT)

SupportCaseCollection type

- `collection` → `[SupportCase!]!`
  - A collection of paginated SupportCaseCollection
- `metadata` → `CollectionMetadata!`
  - Pagination Metadata for navigating the Pagination

### SupportCaseFile (OBJECT)

Mapbiomas SupportCaseFile

- `fileType` → `SupportCaseFileTypes!`
- `fileUploadedUrl` → `String`
- `id` → `Int!`
- `name` → `String!`
- `storageName` → `String!`
- `supportCase` → `SupportCase!`
- `supportCaseId` → `Int!`

### SupportCaseFileTypes (ENUM)

Mapbiomas SupportCaseFileTypes

- `Shapefile`
- `Authorization`
- `Others`
- `Removed`

### SupportCaseMessage (OBJECT)

Mapbiomas SupportCaseMessage

- `createdAt` → `BaseDateTime`
- `id` → `Int!`
- `message` → `String`
- `supportCase` → `SupportCase`
- `supportCaseId` → `Int`
- `userId` → `Int`
- `userName` → `String`
- `workspaceUserId` → `Int`

### SupportCaseStatus (OBJECT)

Mapbiomas SupportCaseStatus

- `createdAt` → `BaseDateTime`
- `id` → `Int!`
- `observation` → `String`
- `supportCase` → `SupportCase`
- `supportCaseId` → `Int`
- `supportCaseStatus` → `String`
- `workspaceUserId` → `Int`
- `workspaceUserName` → `String`

### SupportCaseTypes (ENUM)

Mapbiomas SupportCaseTypes

- `Others`
- `AlertReport`
- `AuthorizationRequest`

### TermOfUse (OBJECT)

Mapbiomas TermOfUse

- `destination` → `TermOfUseEnum!`
- `englishContent` → `String`
- `id` → `Int!`
- `indonesianContent` → `String`
- `portugueseContent` → `String`
- `status` → `Int`
- `version` → `Int`

### TermOfUseEnum (ENUM)

Term of use enum

- `Main`
- `AuthorizationRequest`

### Territory (OBJECT)

Mapbiomas Alerta Territory

- `areaHa` → `Float!`
- `boundingBox` → `[Float!]!`
- `category` → `String!`
- `categoryName` → `String!`
- `code` → `String!`
- `id` → `Int!`
- `name` → `String!`

### TerritoryCategory (OBJECT)

Mapbiomas Alerta Territory Category

- `category` → `String!`
- `categoryName` → `String!`
- `territories` → `[TerritoryOption!]`

### TerritoryOption (OBJECT)

Mapbiomas Alerta Territory Option

- `code` → `Int!`
- `name` → `String!`

### User (OBJECT)

User

- `actionsBatches` → `[ActionsBatch!]`
- `avatarUrl` → `String`
- `confirmedAt` → `BaseDateTime`
- `createdAt` → `BaseDateTime`
- `declaredInstitution` → `String`
- `email` → `String`
- `id` → `Int!`
- `institution` → `Institution`
- `institutionId` → `Int`
- `lastLoginAt` → `BaseDateTime`
- `lastTermOfUseVersionSigned` → `Int`
- `lastUpdatedPasswordAt` → `BaseDateTime`
- `name` → `String`
- `profile` → `String`
- `profileCode` → `Int`
- `receiveNotifications` → `Boolean`
- `status` → `String`
- `termOfUseId` → `Int`
- `territories` → `[TerritoryOption!]`
- `updatedAt` → `BaseDateTime`

### WarningLabel (OBJECT)

Warning label

- `en` → `String!`
- `pt` → `String!`

### source_key (ENUM)

- `PRIORITY_MUNICIPALITY`
- `FEDERAL_INFRACTION`
- `STATES_INFRACTION`
- `EMBARGOED_AREA`
- `BIOME`
- `STATE_DEFORESTATION_AUTHORIZATION`
- `DEFORESTATION_AUTHORIZATION`
- `AMACRO`
- `STATES_EMBARGOED`
- `PNRH_LEVEL_1_BASIN`
- `LEGAL_RESERVE`
- `RIVER_SOURCES`
- `WHITE_2023`
- `SIGEF`
- `LEVEL_1_BASIN`
- `SIGEF_PRIVADO`
- `SIGEF_PUBLICO`
- `COASTAL_AND_MARINE_SYSTEM`
- `MUNICIPALITY`
- `CAR`
- `INTERSECTING_CARS`
- `PRIORITY_BIO_CONSERVATION_AREA`
- `ARCHAEOLOGICAL_SITE`
- `CONSERVATION_UNIT`
- `FOREST_MANAGEMENT_PLAN`
- `WATERSHEDS`
- `PERMANENT_PROTECTED_AREA`
- `PUBLIC_FOREST`
- `FEDERAL_PROTECTED_AREA_INTEGRAL_PROTECTION`
- `LEGAL_AMAZON`
- `MUNICIPALITY_PROTECTED_AREA_INTEGRAL_PROTECTION`
- `VEGETATION_MAP`
- `PNRH_LEVEL_2_BASIN`
- `SNCI_PRIVADO`
- `SNCI_PUBLICO`
- `LEVEL_2_BASIN`
- `SICAR_PCT`
- `SEMIARIDO`
- `MATOPIBA`
- `STATE`
- `SICAR_AST`
- `ANA_2021`
- `SICAR_IRU`
- `SNCI`
- `FEDERAL_PROTECTED_AREA_SUSTAINABLE_USE`
- `STATE_PROTECTED_AREA_INTEGRAL_PROTECTION`
- `STATE_PROTECTED_AREA_SUSTAINABLE_USE`
- `COUNTRY`
- `BIOSPHERE_RESERVE`
- `MMA_2021`
- `SFB_2022`
- `INCRA_2021`
- `MUNICIPALITY_PROTECTED_AREA_SUSTAINABLE_USE`
- `GEOPARK`
- `ATLANTIC_FOREST_LAW`
- `OPEN_STREET_2023`
- `ARCGIS`
- `PLANET`
- `STATES_PROTECTED_AREA`
- `QUILOMBO`
- `IBGE_2021`
- `INPE_TB`
- `INDIGENOUS_LAND`
- `SETTLEMENT`
- `UNESCO_2021`
- `SFB_2021`
- `FUNAI_2021`
- `GOOGLE_STREET_2023`
- `MAPBIOMAS_2023`
- `CITY`
- `BOLSA_VERDE_PROGRAM`
- `REFINED_BIOME`
- `SPECIAL_TERRITORY`
- `AMAZONIA_LEGAL`
- `LEI_DA_MATA_ATLANTICA`
