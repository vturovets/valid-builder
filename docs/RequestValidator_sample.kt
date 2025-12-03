package com.xyz.holidayoffers.adapter.`in`.rest.validation

import com.xyz.holidayoffers.config.BrandMapping
import com.xyz.holidayoffers.config.BrandMapping.isNordics
import com.xyz.holidayoffers.config.ChannelConfig
import com.xyz.holidayoffers.config.LocaleLangMapping
import com.xyz.holidayoffers.domain.ListOfferChannel
import com.xyz.holidayoffers.domain.SiteID
import com.xyz.holidayoffers.domain.exception.HolidayOffersValidationException
import com.xyz.holidayoffers.proxy.generated.model.*
import io.micronaut.http.HttpStatus
import jakarta.inject.Singleton
import java.math.BigDecimal
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.time.format.DateTimeParseException
import mu.KotlinLogging

private val logger = KotlinLogging.logger { }

@Singleton
class RequestValidator(
    private val channelConfig: ChannelConfig,
) {
    companion object {
        const val HOF_VALIDATION_FAILED = "Validation failed for Holiday Offers request"
        const val UOF_VALIDATION_FAILED = "Validation failed for Unique Offer request"
        const val VALIDATION_FAILED = "Validation failed for '%s' field"
        const val INVALID_DATE_FORMAT = "Invalid date format for '%s' value"
        const val INVALID_DATE_RANGE = "The 'from' date '%s' value must be before the 'to' date '%s' value"
        const val DATE_IN_PAST = "The date '%s' is in the past"
        private val DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd")
        private val ADULT_AGE_THRESHOLD = BigDecimal(17)
        const val PAX_NUMBERS = 9
        const val DUPLICATE_FILTERS = "Duplicate filters in the request: %s"
        const val SELECTED_UNAVAILABLE = "Selected unavailable options in the filters: %s"
        const val NEGATIVE_AGE = "cannot be negative, found: %s"
        const val UNIT_ALLOCATION_NEGATIVE_AGE = "UnitAllocation 'paxAge' $NEGATIVE_AGE"
        const val UNIT_ALLOCATION_MANDATORY = "'unitAllocations' is mandatory if the number of passengers exceeds 9!"
        const val TRAVELLER_NEGATIVE_AGE = "Travellers 'age' $NEGATIVE_AGE"
        const val ID_ERROR = "must be greater than or equal to 1, found: %s"
        const val TRAVELLER_ID_ERROR = "Travellers 'id' $ID_ERROR"
        const val UNIT_ALLOCATION_PAX_ID_ERROR = "UnitAllocation 'paxID' $ID_ERROR}"
        const val ID_FORMAT = "must be in the number format, found: %s"
        const val TRAVELLER_ID_FORMAT = "Traveller 'id' $ID_FORMAT"
        const val TRAVELLER_ID_NOT_EXISTS_IN = "Referenced traveller 'id' doesn't exist in 'travellers': %s"
        const val ADULTS_ARE_ABSENT = "Adults are absent in the '%s'"
        const val INVALID_TRAVELLERS_COUNT = "Invalid 'travellers' count: must be equal for '%s' count"
        const val AGENT_ID_REQUIRED = "'metaInformation.agentId' is required for NR and target=B2B."
        const val FILTER_IS_AVAILABLE_ONLY_FOR_NOR = "Filter '%s' is available only for Nordics: NO, FI, DK, SE"
        const val FILTER_IS_NOT_AVAILABLE_NOR = "Filter '%s' is not available for Nordics: NO, FI, DK, SE"

        const val HOF = "Holiday Offers"
        const val UOF = "Unique Offer"
        const val PRC = "Price Calendar"
        const val DUR = "Durations"
        const val DUR_VALIDATION_FAILED = "Validation failed for Durations request"
        const val ALT_DUR = "Alt Durations"
        const val ALT_DUR_VALIDATION_FAILED = "Validation failed for Alt Durations request"

        val nordicsOnlyFilters =
            setOf(
                FilterType.CUSTOMERRATING,
                FilterType.DISTANCETO,
                FilterType.PRICE,
            )

        val ukiOnlyFilters =
            setOf(
                FilterType.PRICEPP,
            )

        fun throwValidationException(
            error: String,
            errorTitle: String,
            errorSystem: String?,
        ): Nothing {
            logger.error(error)
            throw HolidayOffersValidationException(
                status = HttpStatus.BAD_REQUEST,
                problem =
                    ValidationProblem(
                        problem =
                            Problem(
                                title = errorTitle,
                                system = errorSystem,
                            ),
                        validationIssues = listOf(error),
                    ),
            )
        }
    }

    fun validateChannelRequest(channel: ListOfferChannel) {
        val region = SiteID.valueOf(channel.siteID.uppercase()).getRegion()
        if (shouldValidateChannelMapping(region)) {
            validateChannelMapping(channel.target, channel.medium)
        }
    }

    private fun shouldValidateChannelMapping(region: String): Boolean = region == "wr" && channelConfig.beneAdminFeesFeatureFlag

    private fun validateChannelMapping(
        target: String,
        medium: String,
    ) {
        val targetKey = target.lowercase()
        val mediumValue = medium.uppercase()

        val isValidMapping =
            channelConfig.targetToMediumMap[targetKey]
                ?.contains(mediumValue) == true

        if (!isValidMapping) {
            throwValidationException(
                "Invalid channel mapping for target: $target and medium: $medium",
                HOF_VALIDATION_FAILED,
                HOF,
            )
        }
    }


}
