# Answer Method (discoveryengine API) Configuration Options (Python)

[← Back to README](../../README.md)

The Discovery Engine API [`answer` method](https://cloud.google.com/generative-ai-app-builder/docs/answer) accepts a variety of configuration options to customize the search and answer generation phases. The following Python code snippet demonstrates how to configure the `answer` method with the available options.

The [Python client library](https://cloud.google.com/python/docs/reference/discoveryengine/latest) does not currently implement all of the features available in the [RPC API](https://cloud.google.com/python/docs/reference/discoveryengine/latest). ([`SafetySetting`](https://cloud.google.com/generative-ai-app-builder/docs/reference/rpc/google.cloud.discoveryengine.v1#safetysetting), for [example](https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.AnswerQueryRequest.SafetySpec))


```py
async def answer_query(
    self,
    query_text: str,
    session_id: str | None,
) -> AnswerQueryResponse:
    """Call the answer method and return a generated answer and a list of search results,
    with links to the sources.

    Args:
        query_text (str): The text of the query to be answered.
        session_id (str, optional): The session ID to continue a conversation.

    Returns:
        AnswerQueryResponse: The response from the Conversational Search Service,
        containing the generated answer and selected references.

    Refs:
    https://cloud.google.com/generative-ai-app-builder/docs/answer#search-answer-basic
    https://cloud.google.com/python/docs/reference/discoveryengine/latest/google.cloud.discoveryengine_v1.types.AnswerQueryRequest
    """
    # serving_config.
    engine = f"projects/{self._project_id}/locations/{self._location}/collections/default_collection/engines/{self._engine_id}"
    serving_config = f"{engine}/servingConfigs/default_serving_config"

    # Query: accepts one of `text` or `query_id`.
    query = discoveryengine.Query(text=query_text)
    # query = discoveryengine.Query(query_id="query_id")

    # session - construct the name using the engine as the serving config.
    session = f"{engine}/sessions/{session_id}" if session_id else None

    # SafetySpec - options for search phase.
    safety_spec = discoveryengine.AnswerQueryRequest.SafetySpec(enable=False)

    # RelatedQuestionsSpec.
    related_questions_spec = discoveryengine.AnswerQueryRequest.RelatedQuestionsSpec(enable=False)

    # AnswerGenerationSpec - options for answer phase.
    answer_generation_spec = discoveryengine.AnswerQueryRequest.AnswerGenerationSpec(
        model_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.ModelSpec(
            model_version="gemini-1.5-flash-001/answer_gen/v2",
        ),
        prompt_spec=discoveryengine.AnswerQueryRequest.AnswerGenerationSpec.PromptSpec(
            preamble=self._preamble,
        ),
        include_citations=True,
        answer_language_code="en",
        ignore_adversarial_query=False,
        ignore_non_answer_seeking_query=False,
        ignore_low_relevant_content=False,  # Optional: Return fallback answer when content is not relevant
        ignore_jail_breaking_query=False,
    )

    # SearchSpec - options for search phase.
    search_spec = discoveryengine.AnswerQueryRequest.SearchSpec(
        # one of `search_params` or `search_result_list` must be set.
        search_params=discoveryengine.AnswerQueryRequest.SearchSpec.SearchParams(
            max_return_results=10,
            filter="filter_expression",
            boost_spec=discoveryengine.SearchRequest.BoostSpec(
                condition_boost_specs=[
                    discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec(
                        condition="condition_1",
                        boost=0.0,
                        boost_control_spec=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec(
                            field_name="boost_field_1",
                            # select one attribute_type
                            attribute_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.AttributeType.ATTRIBUTE_TYPE_UNSPECIFIED,
                            # attribute_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.AttributeType.NUMERICAL,
                            # attribute_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.AttributeType.FRESHNESS,
                            # select one interpolation_type
                            interpolation_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.InterpolationType.INTERPOLATION_TYPE_UNSPECIFIED,
                            # interpolation_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.InterpolationType.LINEAR,
                            control_points=[
                                discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.ControlPoint(
                                    attribute_value="value_1",
                                    boost_amount=0.0,
                                ),
                                discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.ControlPoint(
                                    attribute_value="value_2",
                                    boost_amount=0.0,
                                ),
                            ],
                        ),
                    ),
                    discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec(
                        condition="condition_2",
                        boost=0.0,
                        boost_control_spec=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec(
                            field_name="boost_field_2",
                            # select one attribute_type
                            attribute_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.AttributeType.ATTRIBUTE_TYPE_UNSPECIFIED,
                            # attribute_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.AttributeType.NUMERICAL,
                            # attribute_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.AttributeType.FRESHNESS,
                            # select one interpolation_type
                            interpolation_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.InterpolationType.INTERPOLATION_TYPE_UNSPECIFIED,
                            # interpolation_type=discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.InterpolationType.LINEAR,
                            control_points=[
                                discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.ControlPoint(
                                    attribute_value="value_1",
                                    boost_amount=0.0,
                                ),
                                discoveryengine.SearchRequest.BoostSpec.ConditionBoostSpec.BoostControlSpec.ControlPoint(
                                    attribute_value="value_2",
                                    boost_amount=0.0,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
            order_by="field_name_for_ordering",
            # select one search_result_mode
            search_result_mode=discoveryengine.SearchRequest.ContentSearchSpec.SearchResultMode.DOCUMENTS,
            # search_result_mode=discoveryengine.SearchRequest.ContentSearchSpec.SearchResultMode.SEARCH_RESULT_MODE_UNSPECIFIED,
            # search_result_mode=discoveryengine.SearchRequest.ContentSearchSpec.SearchResultMode.CHUNKS,
            data_store_specs=[
                discoveryengine.SearchRequest.DataStoreSpec(
                    data_store="projects/{project}/locations/{location}/collections/{collection_id}/dataStores/{data_store_id}",
                    filter="filter_expression",
                )
            ],
        ),
        # search_result_list=discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList(
        #     search_results=[
        #         discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult(
        #             unstructured_document_info=discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo(
        #                 document="document_resource_name",
        #                 uri="document_uri",
        #                 title="document_title",
        #                 document_contexts=[
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.DocumentContext(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.DocumentContext(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                 ],
        #                 extractive_segments=[
        #                     # Guide <https://cloud.google.com/generative-ai-app-builder/docs/snippets#extractive-segments>
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.ExtractiveSegment(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.ExtractiveSegment(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                 ],
        #                 extractive_answers=[
        #                     # Guide <https://cloud.google.com/generative-ai-app-builder/docs/snippets#get-answers>
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.ExtractiveAnswer(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.ExtractiveAnswer(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                 ],
        #             ),
        #             chunk_info=discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.ChunkInfo(
        #                 chunk="chunk_resource_name",
        #                 content="chunk_content",
        #                 document_metadata=discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.ChunkInfo.DocumentMetadata(
        #                     uri="document_uri",
        #                     title="document_title",
        #                 ),
        #             ),
        #         ),
        #         discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult(
        #             unstructured_document_info=discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo(
        #                 document="document_resource_name",
        #                 uri="document_uri",
        #                 title="document_title",
        #                 document_contexts=[
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.DocumentContext(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.DocumentContext(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                 ],
        #                 extractive_segments=[
        #                     # Guide <https://cloud.google.com/generative-ai-app-builder/docs/snippets#extractive-segments>
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.ExtractiveSegment(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.ExtractiveSegment(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                 ],
        #                 extractive_answers=[
        #                     # Guide <https://cloud.google.com/generative-ai-app-builder/docs/snippets#get-answers>
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.ExtractiveAnswer(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                     discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.UnstructuredDocumentInfo.ExtractiveAnswer(
        #                         page_identifier="page_identifier",
        #                         content="content",
        #                     ),
        #                 ],
        #             ),
        #             chunk_info=discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.ChunkInfo(
        #                 chunk="chunk_resource_name",
        #                 content="chunk_content",
        #                 document_metadata=discoveryengine.AnswerQueryRequest.SearchSpec.SearchResultList.SearchResult.ChunkInfo.DocumentMetadata(
        #                     uri="document_uri",
        #                     title="document_title",
        #                 ),
        #             ),
        #         ),
        #     ]
        # ),
    )

    # QueryUnderstandingSpec - options for query phase.
    query_understanding_spec = discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec(
        query_classification_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec(
            types=[
                discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.TYPE_UNSPECIFIED,
                discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.ADVERSARIAL_QUERY,
                discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.NON_ANSWER_SEEKING_QUERY,
                discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.JAIL_BREAKING_QUERY,
                discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryClassificationSpec.Type.NON_ANSWER_SEEKING_QUERY_V2,
            ]
        ),
        query_rephraser_spec=discoveryengine.AnswerQueryRequest.QueryUnderstandingSpec.QueryRephraserSpec(
            disable=False,
            max_rephrase_steps=1, # max allowed is 5 steps
        ),
        
    )

    # user_pseudo_id.
    user_pseudo_id = "user_pseudo_id"

    # user_labels.
    user_labels = {"key": "value"}

    # Initialize request argument(s).
    request = discoveryengine.AnswerQueryRequest(
        serving_config=serving_config,
        query=query,
        session=session,
        safety_spec=safety_spec,
        related_questions_spec=related_questions_spec,
        answer_generation_spec=answer_generation_spec,
        search_spec=search_spec,
        query_understanding_spec=query_understanding_spec,
        user_pseudo_id=user_pseudo_id,
        user_labels=user_labels,
    )

    # Make the request.
    response = await self._client.answer_query(request)

    # Handle the response.
    logger.debug(response)
    logger.info(f"Answer: {response.answer.answer_text}")

    return response
```
