import * as React from 'react'
import { useSelector } from 'react-redux'
import { Card } from '@opentrons/components'
import {
  MAGNETIC_MODULE_TYPE,
  TEMPERATURE_MODULE_TYPE,
  ModuleType,
} from '@opentrons/shared-data'
import {
  selectors as stepFormSelectors,
  getIsCrashablePipetteSelected,
  ModulesForEditModulesCard,
} from '../../step-forms'
import { selectors as featureFlagSelectors } from '../../feature-flags'
import { SUPPORTED_MODULE_TYPES } from '../../modules'
import { CrashInfoBox } from './CrashInfoBox'
import { ModuleRow } from './ModuleRow'
import { isModuleWithCollisionIssue } from './utils'
import styles from './styles.css'

export interface Props {
  modules: ModulesForEditModulesCard
  openEditModuleModal: (moduleType: ModuleType, moduleId?: string) => unknown
}

export function EditModulesCard(props: Props): JSX.Element {
  const { modules, openEditModuleModal } = props

  const pipettesByMount = useSelector(
    stepFormSelectors.getPipettesForEditPipetteForm
  )

  const magneticModuleOnDeck = modules[MAGNETIC_MODULE_TYPE]
  const temperatureModuleOnDeck = modules[TEMPERATURE_MODULE_TYPE]

  const hasCrashableMagneticModule =
    magneticModuleOnDeck &&
    isModuleWithCollisionIssue(magneticModuleOnDeck.model)
  const hasCrashableTempModule =
    temperatureModuleOnDeck &&
    isModuleWithCollisionIssue(temperatureModuleOnDeck.model)

  const moduleRestrictionsDisabled = Boolean(
    useSelector(featureFlagSelectors.getDisableModuleRestrictions)
  )
  const crashablePipettesSelected = getIsCrashablePipetteSelected(
    pipettesByMount
  )

  const warningsEnabled =
    !moduleRestrictionsDisabled && crashablePipettesSelected
  const showCrashInfoBox =
    warningsEnabled && (hasCrashableMagneticModule || hasCrashableTempModule)

  return (
    <Card title="Modules">
      <div className={styles.modules_card_content}>
        {showCrashInfoBox && (
          <CrashInfoBox
            magnetOnDeck={hasCrashableMagneticModule}
            temperatureOnDeck={hasCrashableTempModule}
          />
        )}
        {SUPPORTED_MODULE_TYPES.map((moduleType, i) => {
          const moduleData = modules[moduleType]
          if (moduleData) {
            return (
              <ModuleRow
                type={moduleType}
                moduleOnDeck={moduleData}
                showCollisionWarnings={warningsEnabled}
                key={i}
                openEditModuleModal={openEditModuleModal}
              />
            )
          } else {
            return (
              <ModuleRow
                type={moduleType}
                key={i}
                openEditModuleModal={openEditModuleModal}
              />
            )
          }
        })}
      </div>
    </Card>
  )
}
