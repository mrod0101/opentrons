import * as React from 'react'
import {
  ALIGN_CENTER,
  DIRECTION_COLUMN,
  Flex,
  FONT_WEIGHT_SEMIBOLD,
  JUSTIFY_CENTER,
  JUSTIFY_SPACE_BETWEEN,
  PrimaryBtn,
  SPACING_3,
  SPACING_4,
  Text,
  TEXT_TRANSFORM_UPPERCASE,
  C_BLUE,
} from '@opentrons/components'
import { LabwarePositionCheckStepDetail } from './LabwarePositionCheckStepDetail'
import { SectionList } from './SectionList'
import { useIntroInfo, useLabwareIdsBySection } from './hooks'
import { DeckMap } from './DeckMap'
import type { Jog } from '../../../molecules/JogControls'
import type { LabwarePositionCheckStep } from './types'

interface GenericStepScreenProps {
  selectedStep: LabwarePositionCheckStep
  ctaText: string
  proceed: () => void
  jog: Jog
  title: string
}
export const GenericStepScreen = (
  props: GenericStepScreenProps
): JSX.Element | null => {
  const introInfo = useIntroInfo()
  const labwareIdsBySection = useLabwareIdsBySection()
  const [sectionIndex] = React.useState<number>(0)
  if (introInfo == null) return null
  const { sections, primaryPipetteMount, secondaryPipetteMount } = introInfo
  const labwareIdsToHighlight = labwareIdsBySection[props.selectedStep.section]
  const currentSectionIndex = sections.findIndex(
    section => section === props.selectedStep.section
  )
  const completedSections = sections.slice(0, currentSectionIndex)

  return (
    <Flex margin={SPACING_3} flexDirection={DIRECTION_COLUMN}>
      <Text
        as={'h3'}
        textTransform={TEXT_TRANSFORM_UPPERCASE}
        fontWeight={FONT_WEIGHT_SEMIBOLD}
        marginBottom={SPACING_3}
        marginLeft={SPACING_3}
      >
        {props.title}
      </Text>
      <Flex
        justifyContent={JUSTIFY_SPACE_BETWEEN}
        alignItems={ALIGN_CENTER}
        margin={SPACING_3}
      >
        <Flex flexDirection={DIRECTION_COLUMN}>
          <Flex marginLeft={SPACING_4}>
            <SectionList
              primaryPipetteMount={primaryPipetteMount}
              secondaryPipetteMount={secondaryPipetteMount}
              sections={sections}
              currentSection={props.selectedStep.section}
              completedSections={completedSections}
            />
          </Flex>
          <Flex justifyContent={JUSTIFY_CENTER}>
            <DeckMap
              labwareIdsToHighlight={labwareIdsToHighlight}
              completedLabwareIdSections={
                labwareIdsBySection[sections[sectionIndex - 1]]
              }
            />
          </Flex>
        </Flex>
        <Flex padding={SPACING_3}>
          <LabwarePositionCheckStepDetail
            selectedStep={props.selectedStep}
            jog={props.jog}
          />
        </Flex>
      </Flex>
      <Flex justifyContent={JUSTIFY_CENTER} marginBottom={SPACING_4}>
        <PrimaryBtn backgroundColor={C_BLUE} onClick={props.proceed}>
          {props.ctaText}
        </PrimaryBtn>
      </Flex>
    </Flex>
  )
}
