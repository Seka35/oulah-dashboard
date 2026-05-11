--
-- PostgreSQL database dump
--

\restrict LjHOHtXijc21v81tOEJLhACub6kbOwa51GQeJIRvM2orZiyDjdzKmGzQ2s4kNbF

-- Dumped from database version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: ad_cards; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.ad_cards (
    id integer NOT NULL,
    ad_archive_id character varying(255),
    card_index integer,
    title text,
    body text,
    cta_type character varying(255),
    cta_text text,
    caption text,
    link_url text,
    link_description text,
    video_hd_url text,
    video_sd_url text,
    video_preview_image_url text,
    watermarked_video_hd_url text,
    watermarked_video_sd_url text,
    original_image_url text,
    resized_image_url text,
    watermarked_resized_image_url text,
    image_crops jsonb
);


ALTER TABLE public.ad_cards OWNER TO "anon-404";

--
-- Name: ad_cards_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.ad_cards_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ad_cards_id_seq OWNER TO "anon-404";

--
-- Name: ad_cards_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.ad_cards_id_seq OWNED BY public.ad_cards.id;


--
-- Name: ad_categories; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.ad_categories (
    ad_archive_id character varying(255) NOT NULL,
    category character varying(255) NOT NULL
);


ALTER TABLE public.ad_categories OWNER TO "anon-404";

--
-- Name: ad_creatives; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.ad_creatives (
    id integer NOT NULL,
    card_id integer,
    ad_archive_id character varying(255),
    type character varying(50),
    original_url text,
    local_path text,
    downloaded_at timestamp without time zone,
    download_failed boolean DEFAULT false,
    file_size_bytes bigint,
    mime_type character varying(255)
);


ALTER TABLE public.ad_creatives OWNER TO "anon-404";

--
-- Name: ad_creatives_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.ad_creatives_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ad_creatives_id_seq OWNER TO "anon-404";

--
-- Name: ad_creatives_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.ad_creatives_id_seq OWNED BY public.ad_creatives.id;


--
-- Name: ad_extra_content; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.ad_extra_content (
    id integer NOT NULL,
    ad_archive_id character varying(255),
    content_type character varying(50),
    content_value text
);


ALTER TABLE public.ad_extra_content OWNER TO "anon-404";

--
-- Name: ad_extra_content_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.ad_extra_content_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ad_extra_content_id_seq OWNER TO "anon-404";

--
-- Name: ad_extra_content_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.ad_extra_content_id_seq OWNED BY public.ad_extra_content.id;


--
-- Name: ad_publisher_platforms; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.ad_publisher_platforms (
    ad_archive_id character varying(255) NOT NULL,
    platform character varying(255) NOT NULL
);


ALTER TABLE public.ad_publisher_platforms OWNER TO "anon-404";

--
-- Name: ad_snapshots; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.ad_snapshots (
    id integer NOT NULL,
    ad_archive_id character varying(255),
    body_text text,
    cta_type character varying(255),
    display_format character varying(255),
    link_url text,
    link_description text,
    title text,
    caption text,
    byline text,
    disclaimer_label text,
    is_reshared boolean,
    root_reshared_post text,
    branded_content text,
    event text,
    page_categories jsonb,
    impressions_text text,
    impressions_index text
);


ALTER TABLE public.ad_snapshots OWNER TO "anon-404";

--
-- Name: ad_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.ad_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ad_snapshots_id_seq OWNER TO "anon-404";

--
-- Name: ad_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.ad_snapshots_id_seq OWNED BY public.ad_snapshots.id;


--
-- Name: ads; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.ads (
    ad_archive_id character varying(255) NOT NULL,
    collation_count integer,
    collation_id character varying(255),
    page_id character varying(255),
    is_active boolean,
    has_user_reported boolean,
    report_count integer,
    gated_type character varying(255),
    is_aaa_eligible boolean,
    contains_digital_created_media boolean,
    contains_sensitive_content boolean,
    start_date timestamp without time zone,
    end_date timestamp without time zone,
    start_date_formatted text,
    end_date_formatted text,
    total_active_time text,
    reach_estimate text,
    currency character varying(10),
    spend text,
    ad_id character varying(255),
    state_media_run_label text,
    hide_data_status text,
    is_violating_eu_siep boolean,
    fev_info text,
    verified_voice_context text,
    url text,
    ad_library_url text,
    "position" integer,
    ads_count integer,
    total integer,
    raw_json jsonb,
    ai_analysis jsonb,
    last_updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    search_keywords text[] DEFAULT '{}'::text[]
);


ALTER TABLE public.ads OWNER TO "anon-404";

--
-- Name: advertiser_tracking; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.advertiser_tracking (
    id integer NOT NULL,
    page_id character varying(255),
    page_name text,
    platform character varying(50),
    ad_count integer DEFAULT 0,
    first_seen_at timestamp without time zone,
    last_seen_at timestamp without time zone,
    active_days integer,
    total_spend_estimate text,
    is_scaling boolean DEFAULT false,
    scaling_score integer DEFAULT 0,
    scaling_tier character varying(20),
    last_calculated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.advertiser_tracking OWNER TO "anon-404";

--
-- Name: advertiser_tracking_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.advertiser_tracking_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.advertiser_tracking_id_seq OWNER TO "anon-404";

--
-- Name: advertiser_tracking_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.advertiser_tracking_id_seq OWNED BY public.advertiser_tracking.id;


--
-- Name: advertisers; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.advertisers (
    page_id character varying(255) NOT NULL,
    page_name text,
    page_alias text,
    page_category text,
    page_like_count integer,
    page_is_deleted boolean,
    page_is_restricted boolean,
    page_profile_uri text,
    page_verification text,
    ig_followers integer,
    ig_username text,
    ig_verification text,
    is_profile_page boolean,
    is_delegate_page_with_linked_primary_profile boolean,
    about_text text,
    profile_photo_url text,
    page_cover_photo_url text,
    raw_json jsonb
);


ALTER TABLE public.advertisers OWNER TO "anon-404";

--
-- Name: ai_analysis_log; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.ai_analysis_log (
    id integer NOT NULL,
    platform character varying(50),
    external_id character varying(255),
    verdict jsonb,
    model character varying(100),
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.ai_analysis_log OWNER TO "anon-404";

--
-- Name: ai_analysis_log_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.ai_analysis_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ai_analysis_log_id_seq OWNER TO "anon-404";

--
-- Name: ai_analysis_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.ai_analysis_log_id_seq OWNED BY public.ai_analysis_log.id;


--
-- Name: amazon_products; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.amazon_products (
    id integer NOT NULL,
    asin character varying(20),
    title text,
    brand text,
    stars numeric(2,1),
    reviews_count integer,
    price text,
    price_amount numeric(10,2),
    thumbnail text,
    category text,
    url text,
    search_keyword text,
    first_seen_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    raw_json jsonb,
    image_url text,
    ai_analysis jsonb,
    search_keywords text[] DEFAULT '{}'::text[]
);


ALTER TABLE public.amazon_products OWNER TO "anon-404";

--
-- Name: amazon_products_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.amazon_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.amazon_products_id_seq OWNER TO "anon-404";

--
-- Name: amazon_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.amazon_products_id_seq OWNED BY public.amazon_products.id;


--
-- Name: automation_keywords; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.automation_keywords (
    id integer NOT NULL,
    category character varying(100),
    keyword text,
    is_active boolean DEFAULT true,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.automation_keywords OWNER TO "anon-404";

--
-- Name: automation_keywords_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.automation_keywords_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.automation_keywords_id_seq OWNER TO "anon-404";

--
-- Name: automation_keywords_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.automation_keywords_id_seq OWNED BY public.automation_keywords.id;


--
-- Name: automation_settings; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.automation_settings (
    id integer NOT NULL,
    is_active boolean DEFAULT false,
    tiktok_frequency_hours integer DEFAULT 24,
    facebook_frequency_hours integer DEFAULT 48,
    etsy_frequency_hours integer DEFAULT 72,
    amazon_frequency_hours integer DEFAULT 72,
    tiktok_max_ads integer DEFAULT 20,
    facebook_max_ads integer DEFAULT 20,
    etsy_max_products integer DEFAULT 20,
    amazon_max_products integer DEFAULT 20,
    last_run_tiktok timestamp without time zone,
    last_run_facebook timestamp without time zone,
    last_run_etsy timestamp without time zone,
    last_run_amazon timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.automation_settings OWNER TO "anon-404";

--
-- Name: automation_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.automation_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.automation_settings_id_seq OWNER TO "anon-404";

--
-- Name: automation_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.automation_settings_id_seq OWNED BY public.automation_settings.id;


--
-- Name: br_transparency; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.br_transparency (
    id integer NOT NULL,
    ad_archive_id character varying(255),
    targets_eu boolean,
    eu_total_reach integer,
    gender_audience text,
    age_min integer,
    age_max integer,
    has_violating_payer_beneficiary boolean,
    is_ad_taken_down boolean
);


ALTER TABLE public.br_transparency OWNER TO "anon-404";

--
-- Name: br_transparency_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.br_transparency_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.br_transparency_id_seq OWNER TO "anon-404";

--
-- Name: br_transparency_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.br_transparency_id_seq OWNED BY public.br_transparency.id;


--
-- Name: crawl_jobs; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.crawl_jobs (
    id integer NOT NULL,
    source character varying(50),
    query text,
    ran_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    total_results integer,
    ads_inserted integer,
    ads_updated integer,
    status character varying(50),
    apify_run_id character varying(255)
);


ALTER TABLE public.crawl_jobs OWNER TO "anon-404";

--
-- Name: crawl_jobs_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.crawl_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.crawl_jobs_id_seq OWNER TO "anon-404";

--
-- Name: crawl_jobs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.crawl_jobs_id_seq OWNED BY public.crawl_jobs.id;


--
-- Name: digital_product_classification; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.digital_product_classification (
    id integer NOT NULL,
    ad_archive_id character varying(255),
    tiktok_ad_id character varying(255),
    classification_type character varying(50),
    confidence_score numeric(3,2),
    matched_keywords text[],
    url_domain text,
    is_digital_product boolean,
    product_category character varying(100),
    product_name text,
    raw_classification jsonb,
    classified_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.digital_product_classification OWNER TO "anon-404";

--
-- Name: digital_product_classification_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.digital_product_classification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.digital_product_classification_id_seq OWNER TO "anon-404";

--
-- Name: digital_product_classification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.digital_product_classification_id_seq OWNED BY public.digital_product_classification.id;


--
-- Name: etsy_products; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.etsy_products (
    id integer NOT NULL,
    listing_id character varying(255),
    title text,
    price text,
    currency character varying(10),
    price_amount numeric(10,2),
    shop_name text,
    shop_url text,
    rating numeric(2,1),
    review_count integer,
    url text,
    search_keyword text,
    first_seen_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    raw_json jsonb,
    image_url text,
    ai_analysis jsonb,
    search_keywords text[] DEFAULT '{}'::text[]
);


ALTER TABLE public.etsy_products OWNER TO "anon-404";

--
-- Name: etsy_products_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.etsy_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.etsy_products_id_seq OWNER TO "anon-404";

--
-- Name: etsy_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.etsy_products_id_seq OWNED BY public.etsy_products.id;


--
-- Name: eu_location_audience; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.eu_location_audience (
    id integer NOT NULL,
    eu_targeting_id integer,
    name text,
    type text,
    excluded boolean,
    num_obfuscated integer
);


ALTER TABLE public.eu_location_audience OWNER TO "anon-404";

--
-- Name: eu_location_audience_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.eu_location_audience_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.eu_location_audience_id_seq OWNER TO "anon-404";

--
-- Name: eu_location_audience_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.eu_location_audience_id_seq OWNED BY public.eu_location_audience.id;


--
-- Name: eu_payer_beneficiary; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.eu_payer_beneficiary (
    id integer NOT NULL,
    eu_targeting_id integer,
    payer text,
    beneficiary text
);


ALTER TABLE public.eu_payer_beneficiary OWNER TO "anon-404";

--
-- Name: eu_payer_beneficiary_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.eu_payer_beneficiary_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.eu_payer_beneficiary_id_seq OWNER TO "anon-404";

--
-- Name: eu_payer_beneficiary_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.eu_payer_beneficiary_id_seq OWNED BY public.eu_payer_beneficiary.id;


--
-- Name: eu_targeting; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.eu_targeting (
    id integer NOT NULL,
    ad_archive_id character varying(255),
    targets_eu boolean,
    eu_total_reach integer,
    gender_audience text,
    age_min integer,
    age_max integer,
    has_violating_payer_beneficiary boolean,
    is_ad_taken_down boolean
);


ALTER TABLE public.eu_targeting OWNER TO "anon-404";

--
-- Name: eu_targeting_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.eu_targeting_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.eu_targeting_id_seq OWNER TO "anon-404";

--
-- Name: eu_targeting_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.eu_targeting_id_seq OWNED BY public.eu_targeting.id;


--
-- Name: google_ad_images; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.google_ad_images (
    id integer NOT NULL,
    ad_id character varying(255),
    image_url text,
    local_path text
);


ALTER TABLE public.google_ad_images OWNER TO "anon-404";

--
-- Name: google_ad_images_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.google_ad_images_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.google_ad_images_id_seq OWNER TO "anon-404";

--
-- Name: google_ad_images_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.google_ad_images_id_seq OWNED BY public.google_ad_images.id;


--
-- Name: google_ads; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.google_ads (
    ad_id character varying(255) NOT NULL,
    search_id integer,
    advertiser_id text,
    creative_id text,
    format text,
    ad_transparency_url text,
    creative_regions text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.google_ads OWNER TO "anon-404";

--
-- Name: keyword_platform_status; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.keyword_platform_status (
    id integer NOT NULL,
    keyword_id integer,
    platform character varying(50),
    last_tested_at timestamp without time zone,
    status character varying(50) DEFAULT 'pending'::character varying
);


ALTER TABLE public.keyword_platform_status OWNER TO "anon-404";

--
-- Name: keyword_platform_status_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.keyword_platform_status_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.keyword_platform_status_id_seq OWNER TO "anon-404";

--
-- Name: keyword_platform_status_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.keyword_platform_status_id_seq OWNED BY public.keyword_platform_status.id;


--
-- Name: landing_pages; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.landing_pages (
    id integer NOT NULL,
    opportunity_id character varying(100),
    url text,
    domain text,
    hero_headline text,
    hero_subheadline text,
    main_offer text,
    price_text text,
    price_amount numeric(10,2),
    currency character varying(10),
    cta_text text,
    cta_url text,
    checkout_type character varying(50),
    checkout_domain character varying(255),
    technology_stack text[],
    trust_signals text[],
    full_text_content text,
    html_content text,
    screenshot_path text,
    scraped_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    scrape_error text
);


ALTER TABLE public.landing_pages OWNER TO "anon-404";

--
-- Name: landing_pages_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.landing_pages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.landing_pages_id_seq OWNER TO "anon-404";

--
-- Name: landing_pages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.landing_pages_id_seq OWNED BY public.landing_pages.id;


--
-- Name: opportunity_creatives; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.opportunity_creatives (
    id integer NOT NULL,
    opportunity_id character varying(100),
    source_ad_archive_id character varying(255),
    source_tiktok_ad_id character varying(255),
    platform character varying(50),
    creative_type character varying(50),
    original_url text,
    local_path text,
    downloaded boolean DEFAULT false,
    ad_first_seen date,
    ad_last_seen date,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.opportunity_creatives OWNER TO "anon-404";

--
-- Name: opportunity_creatives_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.opportunity_creatives_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.opportunity_creatives_id_seq OWNER TO "anon-404";

--
-- Name: opportunity_creatives_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.opportunity_creatives_id_seq OWNED BY public.opportunity_creatives.id;


--
-- Name: page_spend; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.page_spend (
    id integer NOT NULL,
    page_id character varying(255),
    is_political_page boolean,
    current_week_spend jsonb,
    lifetime_by_disclaimer jsonb,
    weekly_by_disclaimer jsonb
);


ALTER TABLE public.page_spend OWNER TO "anon-404";

--
-- Name: page_spend_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.page_spend_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.page_spend_id_seq OWNER TO "anon-404";

--
-- Name: page_spend_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.page_spend_id_seq OWNED BY public.page_spend.id;


--
-- Name: product_criteria; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.product_criteria (
    id integer NOT NULL,
    rule_id character varying(100) NOT NULL,
    rule_type character varying(50) NOT NULL,
    platform character varying(50) NOT NULL,
    category character varying(100),
    keyword character varying(255),
    weight numeric(4,2) DEFAULT 1.0,
    is_exclusion boolean DEFAULT false,
    score_boost integer DEFAULT 0,
    config_key character varying(100),
    config_value numeric(10,4),
    is_active boolean DEFAULT true,
    display_order integer DEFAULT 0,
    description text,
    examples text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.product_criteria OWNER TO "anon-404";

--
-- Name: product_criteria_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.product_criteria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_criteria_id_seq OWNER TO "anon-404";

--
-- Name: product_criteria_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.product_criteria_id_seq OWNED BY public.product_criteria.id;


--
-- Name: product_opportunities; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.product_opportunities (
    id integer NOT NULL,
    opportunity_id character varying(100),
    product_name text,
    product_category character varying(100),
    product_description text,
    price_text text,
    price_amount numeric(10,2),
    advertiser_page_id character varying(255),
    advertiser_name text,
    advertiser_platform character varying(50),
    advertiser_page_url text,
    scaling_score integer DEFAULT 0,
    scaling_tier character varying(20),
    active_days integer,
    ad_count integer,
    is_scaling boolean DEFAULT false,
    landing_page_url text,
    landing_page_scraped boolean DEFAULT false,
    landing_page_score numeric(3,2),
    status character varying(50) DEFAULT 'fresh_lead'::character varying,
    priority integer DEFAULT 5,
    first_detected_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    notes text
);


ALTER TABLE public.product_opportunities OWNER TO "anon-404";

--
-- Name: product_opportunities_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.product_opportunities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_opportunities_id_seq OWNER TO "anon-404";

--
-- Name: product_opportunities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.product_opportunities_id_seq OWNED BY public.product_opportunities.id;


--
-- Name: reach_breakdown; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.reach_breakdown (
    id integer NOT NULL,
    eu_targeting_id integer,
    country character(2),
    age_range text,
    male integer,
    female integer,
    unknown integer,
    total integer
);


ALTER TABLE public.reach_breakdown OWNER TO "anon-404";

--
-- Name: reach_breakdown_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.reach_breakdown_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.reach_breakdown_id_seq OWNER TO "anon-404";

--
-- Name: reach_breakdown_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.reach_breakdown_id_seq OWNED BY public.reach_breakdown.id;


--
-- Name: regional_regulation; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.regional_regulation (
    id integer NOT NULL,
    ad_archive_id character varying(255),
    finserv_is_deemed_finserv boolean,
    finserv_is_limited_delivery boolean,
    tw_anti_scam_is_limited_delivery boolean
);


ALTER TABLE public.regional_regulation OWNER TO "anon-404";

--
-- Name: regional_regulation_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.regional_regulation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.regional_regulation_id_seq OWNER TO "anon-404";

--
-- Name: regional_regulation_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.regional_regulation_id_seq OWNED BY public.regional_regulation.id;


--
-- Name: searches; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.searches (
    id integer NOT NULL,
    search_term text,
    tiktok_country text,
    facebook_country text,
    google_region text,
    max_ads integer,
    results_count integer,
    tiktok_count integer,
    facebook_count integer,
    google_count integer,
    searched_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.searches OWNER TO "anon-404";

--
-- Name: searches_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.searches_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.searches_id_seq OWNER TO "anon-404";

--
-- Name: searches_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.searches_id_seq OWNED BY public.searches.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.settings (
    key text NOT NULL,
    value text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.settings OWNER TO "anon-404";

--
-- Name: targeted_countries; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.targeted_countries (
    ad_archive_id character varying(255) NOT NULL,
    country_code character varying(255) NOT NULL
);


ALTER TABLE public.targeted_countries OWNER TO "anon-404";

--
-- Name: tiktok_ad_details_extra; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.tiktok_ad_details_extra (
    id integer NOT NULL,
    ad_id character varying(255),
    key text,
    value text
);


ALTER TABLE public.tiktok_ad_details_extra OWNER TO "anon-404";

--
-- Name: tiktok_ad_details_extra_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.tiktok_ad_details_extra_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tiktok_ad_details_extra_id_seq OWNER TO "anon-404";

--
-- Name: tiktok_ad_details_extra_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.tiktok_ad_details_extra_id_seq OWNED BY public.tiktok_ad_details_extra.id;


--
-- Name: tiktok_ad_media; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.tiktok_ad_media (
    id integer NOT NULL,
    ad_id character varying(255),
    media_index integer,
    media_type character varying(50),
    original_url text,
    local_path text,
    downloaded_at timestamp without time zone,
    download_failed boolean DEFAULT false,
    file_size_bytes bigint,
    mime_type character varying(255)
);


ALTER TABLE public.tiktok_ad_media OWNER TO "anon-404";

--
-- Name: tiktok_ad_media_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.tiktok_ad_media_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tiktok_ad_media_id_seq OWNER TO "anon-404";

--
-- Name: tiktok_ad_media_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.tiktok_ad_media_id_seq OWNED BY public.tiktok_ad_media.id;


--
-- Name: tiktok_ad_targeting_age; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.tiktok_ad_targeting_age (
    id integer NOT NULL,
    ad_id character varying(255),
    region character varying(10),
    age_13_17 boolean,
    age_18_24 boolean,
    age_25_34 boolean,
    age_35_44 boolean,
    age_45_54 boolean,
    age_55_plus boolean
);


ALTER TABLE public.tiktok_ad_targeting_age OWNER TO "anon-404";

--
-- Name: tiktok_ad_targeting_age_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.tiktok_ad_targeting_age_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tiktok_ad_targeting_age_id_seq OWNER TO "anon-404";

--
-- Name: tiktok_ad_targeting_age_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.tiktok_ad_targeting_age_id_seq OWNED BY public.tiktok_ad_targeting_age.id;


--
-- Name: tiktok_ad_targeting_gender; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.tiktok_ad_targeting_gender (
    id integer NOT NULL,
    ad_id character varying(255),
    region character varying(10),
    female boolean,
    male boolean,
    unknown boolean
);


ALTER TABLE public.tiktok_ad_targeting_gender OWNER TO "anon-404";

--
-- Name: tiktok_ad_targeting_gender_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.tiktok_ad_targeting_gender_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tiktok_ad_targeting_gender_id_seq OWNER TO "anon-404";

--
-- Name: tiktok_ad_targeting_gender_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.tiktok_ad_targeting_gender_id_seq OWNED BY public.tiktok_ad_targeting_gender.id;


--
-- Name: tiktok_ad_targeting_regions; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.tiktok_ad_targeting_regions (
    id integer NOT NULL,
    ad_id character varying(255),
    region character varying(10),
    impressions_range text
);


ALTER TABLE public.tiktok_ad_targeting_regions OWNER TO "anon-404";

--
-- Name: tiktok_ad_targeting_regions_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.tiktok_ad_targeting_regions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tiktok_ad_targeting_regions_id_seq OWNER TO "anon-404";

--
-- Name: tiktok_ad_targeting_regions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.tiktok_ad_targeting_regions_id_seq OWNED BY public.tiktok_ad_targeting_regions.id;


--
-- Name: tiktok_ads; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.tiktok_ads (
    ad_id character varying(255) NOT NULL,
    advertiser_name text,
    ad_preview_url text,
    ad_preview_local_path text,
    first_shown_date text,
    first_shown_timestamp bigint,
    last_shown_date text,
    last_shown_timestamp bigint,
    ad_audience text,
    ad_type text,
    audit_status text,
    spent text,
    impression text,
    sponsor text,
    target_audience_size text,
    ad_detail_url text,
    raw_json jsonb,
    ai_analysis jsonb,
    last_updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    search_keywords text[] DEFAULT '{}'::text[]
);


ALTER TABLE public.tiktok_ads OWNER TO "anon-404";

--
-- Name: uk_transparency; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.uk_transparency (
    id integer NOT NULL,
    ad_archive_id character varying(255),
    targets_eu boolean,
    eu_total_reach integer,
    gender_audience text,
    age_min integer,
    age_max integer,
    has_violating_payer_beneficiary boolean,
    is_ad_taken_down boolean
);


ALTER TABLE public.uk_transparency OWNER TO "anon-404";

--
-- Name: uk_transparency_id_seq; Type: SEQUENCE; Schema: public; Owner: anon-404
--

CREATE SEQUENCE public.uk_transparency_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.uk_transparency_id_seq OWNER TO "anon-404";

--
-- Name: uk_transparency_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: anon-404
--

ALTER SEQUENCE public.uk_transparency_id_seq OWNED BY public.uk_transparency.id;


--
-- Name: unified_ads; Type: VIEW; Schema: public; Owner: anon-404
--

CREATE VIEW public.unified_ads AS
 SELECT ads.ad_archive_id AS id,
    'facebook'::text AS source,
    ads.ad_archive_id AS source_ad_id,
    a.page_name AS advertiser_name,
    ads.start_date_formatted AS first_seen,
    ads.end_date_formatted AS last_seen,
    ads.is_active,
    ( SELECT jsonb_agg(ad_publisher_platforms.platform) AS jsonb_agg
           FROM public.ad_publisher_platforms
          WHERE ((ad_publisher_platforms.ad_archive_id)::text = (ads.ad_archive_id)::text)) AS platform_list,
    ads.reach_estimate,
    ads.spend,
    NULL::text AS preview_local_path,
    ads.ad_library_url AS detail_url,
    CURRENT_TIMESTAMP AS created_at
   FROM (public.ads
     LEFT JOIN public.advertisers a ON (((ads.page_id)::text = (a.page_id)::text)))
UNION ALL
 SELECT tiktok_ads.ad_id AS id,
    'tiktok'::text AS source,
    tiktok_ads.ad_id AS source_ad_id,
    tiktok_ads.advertiser_name,
    tiktok_ads.first_shown_date AS first_seen,
    tiktok_ads.last_shown_date AS last_seen,
    NULL::boolean AS is_active,
    '["tiktok"]'::jsonb AS platform_list,
    tiktok_ads.ad_audience AS reach_estimate,
    tiktok_ads.spent AS spend,
    tiktok_ads.ad_preview_local_path AS preview_local_path,
    tiktok_ads.ad_detail_url AS detail_url,
    CURRENT_TIMESTAMP AS created_at
   FROM public.tiktok_ads;


ALTER VIEW public.unified_ads OWNER TO "anon-404";

--
-- Name: violation_types; Type: TABLE; Schema: public; Owner: anon-404
--

CREATE TABLE public.violation_types (
    ad_archive_id character varying(255) NOT NULL,
    violation_type character varying(255) NOT NULL
);


ALTER TABLE public.violation_types OWNER TO "anon-404";

--
-- Name: ad_cards id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_cards ALTER COLUMN id SET DEFAULT nextval('public.ad_cards_id_seq'::regclass);


--
-- Name: ad_creatives id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_creatives ALTER COLUMN id SET DEFAULT nextval('public.ad_creatives_id_seq'::regclass);


--
-- Name: ad_extra_content id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_extra_content ALTER COLUMN id SET DEFAULT nextval('public.ad_extra_content_id_seq'::regclass);


--
-- Name: ad_snapshots id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_snapshots ALTER COLUMN id SET DEFAULT nextval('public.ad_snapshots_id_seq'::regclass);


--
-- Name: advertiser_tracking id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.advertiser_tracking ALTER COLUMN id SET DEFAULT nextval('public.advertiser_tracking_id_seq'::regclass);


--
-- Name: ai_analysis_log id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ai_analysis_log ALTER COLUMN id SET DEFAULT nextval('public.ai_analysis_log_id_seq'::regclass);


--
-- Name: amazon_products id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.amazon_products ALTER COLUMN id SET DEFAULT nextval('public.amazon_products_id_seq'::regclass);


--
-- Name: automation_keywords id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.automation_keywords ALTER COLUMN id SET DEFAULT nextval('public.automation_keywords_id_seq'::regclass);


--
-- Name: automation_settings id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.automation_settings ALTER COLUMN id SET DEFAULT nextval('public.automation_settings_id_seq'::regclass);


--
-- Name: br_transparency id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.br_transparency ALTER COLUMN id SET DEFAULT nextval('public.br_transparency_id_seq'::regclass);


--
-- Name: crawl_jobs id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.crawl_jobs ALTER COLUMN id SET DEFAULT nextval('public.crawl_jobs_id_seq'::regclass);


--
-- Name: digital_product_classification id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.digital_product_classification ALTER COLUMN id SET DEFAULT nextval('public.digital_product_classification_id_seq'::regclass);


--
-- Name: etsy_products id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.etsy_products ALTER COLUMN id SET DEFAULT nextval('public.etsy_products_id_seq'::regclass);


--
-- Name: eu_location_audience id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_location_audience ALTER COLUMN id SET DEFAULT nextval('public.eu_location_audience_id_seq'::regclass);


--
-- Name: eu_payer_beneficiary id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_payer_beneficiary ALTER COLUMN id SET DEFAULT nextval('public.eu_payer_beneficiary_id_seq'::regclass);


--
-- Name: eu_targeting id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_targeting ALTER COLUMN id SET DEFAULT nextval('public.eu_targeting_id_seq'::regclass);


--
-- Name: google_ad_images id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.google_ad_images ALTER COLUMN id SET DEFAULT nextval('public.google_ad_images_id_seq'::regclass);


--
-- Name: keyword_platform_status id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.keyword_platform_status ALTER COLUMN id SET DEFAULT nextval('public.keyword_platform_status_id_seq'::regclass);


--
-- Name: landing_pages id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.landing_pages ALTER COLUMN id SET DEFAULT nextval('public.landing_pages_id_seq'::regclass);


--
-- Name: opportunity_creatives id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.opportunity_creatives ALTER COLUMN id SET DEFAULT nextval('public.opportunity_creatives_id_seq'::regclass);


--
-- Name: page_spend id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.page_spend ALTER COLUMN id SET DEFAULT nextval('public.page_spend_id_seq'::regclass);


--
-- Name: product_criteria id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.product_criteria ALTER COLUMN id SET DEFAULT nextval('public.product_criteria_id_seq'::regclass);


--
-- Name: product_opportunities id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.product_opportunities ALTER COLUMN id SET DEFAULT nextval('public.product_opportunities_id_seq'::regclass);


--
-- Name: reach_breakdown id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.reach_breakdown ALTER COLUMN id SET DEFAULT nextval('public.reach_breakdown_id_seq'::regclass);


--
-- Name: regional_regulation id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.regional_regulation ALTER COLUMN id SET DEFAULT nextval('public.regional_regulation_id_seq'::regclass);


--
-- Name: searches id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.searches ALTER COLUMN id SET DEFAULT nextval('public.searches_id_seq'::regclass);


--
-- Name: tiktok_ad_details_extra id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_details_extra ALTER COLUMN id SET DEFAULT nextval('public.tiktok_ad_details_extra_id_seq'::regclass);


--
-- Name: tiktok_ad_media id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_media ALTER COLUMN id SET DEFAULT nextval('public.tiktok_ad_media_id_seq'::regclass);


--
-- Name: tiktok_ad_targeting_age id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_age ALTER COLUMN id SET DEFAULT nextval('public.tiktok_ad_targeting_age_id_seq'::regclass);


--
-- Name: tiktok_ad_targeting_gender id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_gender ALTER COLUMN id SET DEFAULT nextval('public.tiktok_ad_targeting_gender_id_seq'::regclass);


--
-- Name: tiktok_ad_targeting_regions id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_regions ALTER COLUMN id SET DEFAULT nextval('public.tiktok_ad_targeting_regions_id_seq'::regclass);


--
-- Name: uk_transparency id; Type: DEFAULT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.uk_transparency ALTER COLUMN id SET DEFAULT nextval('public.uk_transparency_id_seq'::regclass);


--
-- Name: ad_cards ad_cards_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_cards
    ADD CONSTRAINT ad_cards_pkey PRIMARY KEY (id);


--
-- Name: ad_categories ad_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_categories
    ADD CONSTRAINT ad_categories_pkey PRIMARY KEY (ad_archive_id, category);


--
-- Name: ad_creatives ad_creatives_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_creatives
    ADD CONSTRAINT ad_creatives_pkey PRIMARY KEY (id);


--
-- Name: ad_extra_content ad_extra_content_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_extra_content
    ADD CONSTRAINT ad_extra_content_pkey PRIMARY KEY (id);


--
-- Name: ad_publisher_platforms ad_publisher_platforms_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_publisher_platforms
    ADD CONSTRAINT ad_publisher_platforms_pkey PRIMARY KEY (ad_archive_id, platform);


--
-- Name: ad_snapshots ad_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_snapshots
    ADD CONSTRAINT ad_snapshots_pkey PRIMARY KEY (id);


--
-- Name: ads ads_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ads
    ADD CONSTRAINT ads_pkey PRIMARY KEY (ad_archive_id);


--
-- Name: advertiser_tracking advertiser_tracking_page_id_platform_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.advertiser_tracking
    ADD CONSTRAINT advertiser_tracking_page_id_platform_key UNIQUE (page_id, platform);


--
-- Name: advertiser_tracking advertiser_tracking_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.advertiser_tracking
    ADD CONSTRAINT advertiser_tracking_pkey PRIMARY KEY (id);


--
-- Name: advertisers advertisers_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.advertisers
    ADD CONSTRAINT advertisers_pkey PRIMARY KEY (page_id);


--
-- Name: ai_analysis_log ai_analysis_log_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ai_analysis_log
    ADD CONSTRAINT ai_analysis_log_pkey PRIMARY KEY (id);


--
-- Name: amazon_products amazon_products_asin_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.amazon_products
    ADD CONSTRAINT amazon_products_asin_key UNIQUE (asin);


--
-- Name: amazon_products amazon_products_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.amazon_products
    ADD CONSTRAINT amazon_products_pkey PRIMARY KEY (id);


--
-- Name: amazon_products amazon_products_url_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.amazon_products
    ADD CONSTRAINT amazon_products_url_key UNIQUE (url);


--
-- Name: automation_keywords automation_keywords_keyword_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.automation_keywords
    ADD CONSTRAINT automation_keywords_keyword_key UNIQUE (keyword);


--
-- Name: automation_keywords automation_keywords_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.automation_keywords
    ADD CONSTRAINT automation_keywords_pkey PRIMARY KEY (id);


--
-- Name: automation_settings automation_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.automation_settings
    ADD CONSTRAINT automation_settings_pkey PRIMARY KEY (id);


--
-- Name: br_transparency br_transparency_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.br_transparency
    ADD CONSTRAINT br_transparency_pkey PRIMARY KEY (id);


--
-- Name: crawl_jobs crawl_jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.crawl_jobs
    ADD CONSTRAINT crawl_jobs_pkey PRIMARY KEY (id);


--
-- Name: digital_product_classification digital_product_classification_ad_archive_id_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.digital_product_classification
    ADD CONSTRAINT digital_product_classification_ad_archive_id_key UNIQUE (ad_archive_id);


--
-- Name: digital_product_classification digital_product_classification_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.digital_product_classification
    ADD CONSTRAINT digital_product_classification_pkey PRIMARY KEY (id);


--
-- Name: etsy_products etsy_products_listing_id_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.etsy_products
    ADD CONSTRAINT etsy_products_listing_id_key UNIQUE (listing_id);


--
-- Name: etsy_products etsy_products_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.etsy_products
    ADD CONSTRAINT etsy_products_pkey PRIMARY KEY (id);


--
-- Name: etsy_products etsy_products_url_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.etsy_products
    ADD CONSTRAINT etsy_products_url_key UNIQUE (url);


--
-- Name: eu_location_audience eu_location_audience_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_location_audience
    ADD CONSTRAINT eu_location_audience_pkey PRIMARY KEY (id);


--
-- Name: eu_payer_beneficiary eu_payer_beneficiary_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_payer_beneficiary
    ADD CONSTRAINT eu_payer_beneficiary_pkey PRIMARY KEY (id);


--
-- Name: eu_targeting eu_targeting_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_targeting
    ADD CONSTRAINT eu_targeting_pkey PRIMARY KEY (id);


--
-- Name: google_ad_images google_ad_images_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.google_ad_images
    ADD CONSTRAINT google_ad_images_pkey PRIMARY KEY (id);


--
-- Name: google_ads google_ads_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.google_ads
    ADD CONSTRAINT google_ads_pkey PRIMARY KEY (ad_id);


--
-- Name: keyword_platform_status keyword_platform_status_keyword_id_platform_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.keyword_platform_status
    ADD CONSTRAINT keyword_platform_status_keyword_id_platform_key UNIQUE (keyword_id, platform);


--
-- Name: keyword_platform_status keyword_platform_status_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.keyword_platform_status
    ADD CONSTRAINT keyword_platform_status_pkey PRIMARY KEY (id);


--
-- Name: landing_pages landing_pages_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.landing_pages
    ADD CONSTRAINT landing_pages_pkey PRIMARY KEY (id);


--
-- Name: landing_pages landing_pages_url_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.landing_pages
    ADD CONSTRAINT landing_pages_url_key UNIQUE (url);


--
-- Name: opportunity_creatives opportunity_creatives_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.opportunity_creatives
    ADD CONSTRAINT opportunity_creatives_pkey PRIMARY KEY (id);


--
-- Name: page_spend page_spend_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.page_spend
    ADD CONSTRAINT page_spend_pkey PRIMARY KEY (id);


--
-- Name: product_criteria product_criteria_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.product_criteria
    ADD CONSTRAINT product_criteria_pkey PRIMARY KEY (id);


--
-- Name: product_criteria product_criteria_rule_id_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.product_criteria
    ADD CONSTRAINT product_criteria_rule_id_key UNIQUE (rule_id);


--
-- Name: product_opportunities product_opportunities_opportunity_id_key; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.product_opportunities
    ADD CONSTRAINT product_opportunities_opportunity_id_key UNIQUE (opportunity_id);


--
-- Name: product_opportunities product_opportunities_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.product_opportunities
    ADD CONSTRAINT product_opportunities_pkey PRIMARY KEY (id);


--
-- Name: reach_breakdown reach_breakdown_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.reach_breakdown
    ADD CONSTRAINT reach_breakdown_pkey PRIMARY KEY (id);


--
-- Name: regional_regulation regional_regulation_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.regional_regulation
    ADD CONSTRAINT regional_regulation_pkey PRIMARY KEY (id);


--
-- Name: searches searches_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.searches
    ADD CONSTRAINT searches_pkey PRIMARY KEY (id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (key);


--
-- Name: targeted_countries targeted_countries_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.targeted_countries
    ADD CONSTRAINT targeted_countries_pkey PRIMARY KEY (ad_archive_id, country_code);


--
-- Name: tiktok_ad_details_extra tiktok_ad_details_extra_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_details_extra
    ADD CONSTRAINT tiktok_ad_details_extra_pkey PRIMARY KEY (id);


--
-- Name: tiktok_ad_media tiktok_ad_media_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_media
    ADD CONSTRAINT tiktok_ad_media_pkey PRIMARY KEY (id);


--
-- Name: tiktok_ad_targeting_age tiktok_ad_targeting_age_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_age
    ADD CONSTRAINT tiktok_ad_targeting_age_pkey PRIMARY KEY (id);


--
-- Name: tiktok_ad_targeting_gender tiktok_ad_targeting_gender_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_gender
    ADD CONSTRAINT tiktok_ad_targeting_gender_pkey PRIMARY KEY (id);


--
-- Name: tiktok_ad_targeting_regions tiktok_ad_targeting_regions_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_regions
    ADD CONSTRAINT tiktok_ad_targeting_regions_pkey PRIMARY KEY (id);


--
-- Name: tiktok_ads tiktok_ads_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ads
    ADD CONSTRAINT tiktok_ads_pkey PRIMARY KEY (ad_id);


--
-- Name: uk_transparency uk_transparency_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.uk_transparency
    ADD CONSTRAINT uk_transparency_pkey PRIMARY KEY (id);


--
-- Name: violation_types violation_types_pkey; Type: CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.violation_types
    ADD CONSTRAINT violation_types_pkey PRIMARY KEY (ad_archive_id, violation_type);


--
-- Name: idx_ad_creatives_archive_id; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_ad_creatives_archive_id ON public.ad_creatives USING btree (ad_archive_id);


--
-- Name: idx_amazon_asin; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_amazon_asin ON public.amazon_products USING btree (asin);


--
-- Name: idx_amazon_rating; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_amazon_rating ON public.amazon_products USING btree (stars DESC);


--
-- Name: idx_amazon_reviews; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_amazon_reviews ON public.amazon_products USING btree (reviews_count DESC);


--
-- Name: idx_classification_digital; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_classification_digital ON public.digital_product_classification USING btree (is_digital_product) WHERE (is_digital_product = true);


--
-- Name: idx_creatives_opportunity; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_creatives_opportunity ON public.opportunity_creatives USING btree (opportunity_id);


--
-- Name: idx_criteria_active; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_criteria_active ON public.product_criteria USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_criteria_category; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_criteria_category ON public.product_criteria USING btree (category);


--
-- Name: idx_criteria_platform; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_criteria_platform ON public.product_criteria USING btree (platform);


--
-- Name: idx_criteria_type; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_criteria_type ON public.product_criteria USING btree (rule_type);


--
-- Name: idx_etsy_rating; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_etsy_rating ON public.etsy_products USING btree (rating DESC);


--
-- Name: idx_etsy_reviews; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_etsy_reviews ON public.etsy_products USING btree (review_count DESC);


--
-- Name: idx_etsy_shop; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_etsy_shop ON public.etsy_products USING btree (shop_name);


--
-- Name: idx_landing_pages_domain; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_landing_pages_domain ON public.landing_pages USING btree (domain);


--
-- Name: idx_opportunities_score; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_opportunities_score ON public.product_opportunities USING btree (scaling_score DESC);


--
-- Name: idx_opportunities_status; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_opportunities_status ON public.product_opportunities USING btree (status);


--
-- Name: idx_tiktok_ad_media_ad_id; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_tiktok_ad_media_ad_id ON public.tiktok_ad_media USING btree (ad_id);


--
-- Name: idx_tracking_scaling; Type: INDEX; Schema: public; Owner: anon-404
--

CREATE INDEX idx_tracking_scaling ON public.advertiser_tracking USING btree (is_scaling, scaling_tier);


--
-- Name: ad_cards ad_cards_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_cards
    ADD CONSTRAINT ad_cards_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: ad_categories ad_categories_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_categories
    ADD CONSTRAINT ad_categories_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: ad_creatives ad_creatives_card_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_creatives
    ADD CONSTRAINT ad_creatives_card_id_fkey FOREIGN KEY (card_id) REFERENCES public.ad_cards(id);


--
-- Name: ad_extra_content ad_extra_content_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_extra_content
    ADD CONSTRAINT ad_extra_content_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: ad_publisher_platforms ad_publisher_platforms_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_publisher_platforms
    ADD CONSTRAINT ad_publisher_platforms_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: ad_snapshots ad_snapshots_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ad_snapshots
    ADD CONSTRAINT ad_snapshots_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: ads ads_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.ads
    ADD CONSTRAINT ads_page_id_fkey FOREIGN KEY (page_id) REFERENCES public.advertisers(page_id);


--
-- Name: br_transparency br_transparency_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.br_transparency
    ADD CONSTRAINT br_transparency_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: eu_location_audience eu_location_audience_eu_targeting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_location_audience
    ADD CONSTRAINT eu_location_audience_eu_targeting_id_fkey FOREIGN KEY (eu_targeting_id) REFERENCES public.eu_targeting(id);


--
-- Name: eu_payer_beneficiary eu_payer_beneficiary_eu_targeting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_payer_beneficiary
    ADD CONSTRAINT eu_payer_beneficiary_eu_targeting_id_fkey FOREIGN KEY (eu_targeting_id) REFERENCES public.eu_targeting(id);


--
-- Name: eu_targeting eu_targeting_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.eu_targeting
    ADD CONSTRAINT eu_targeting_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: google_ad_images google_ad_images_ad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.google_ad_images
    ADD CONSTRAINT google_ad_images_ad_id_fkey FOREIGN KEY (ad_id) REFERENCES public.google_ads(ad_id);


--
-- Name: keyword_platform_status keyword_platform_status_keyword_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.keyword_platform_status
    ADD CONSTRAINT keyword_platform_status_keyword_id_fkey FOREIGN KEY (keyword_id) REFERENCES public.automation_keywords(id) ON DELETE CASCADE;


--
-- Name: landing_pages landing_pages_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.landing_pages
    ADD CONSTRAINT landing_pages_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.product_opportunities(opportunity_id);


--
-- Name: opportunity_creatives opportunity_creatives_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.opportunity_creatives
    ADD CONSTRAINT opportunity_creatives_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.product_opportunities(opportunity_id);


--
-- Name: page_spend page_spend_page_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.page_spend
    ADD CONSTRAINT page_spend_page_id_fkey FOREIGN KEY (page_id) REFERENCES public.advertisers(page_id);


--
-- Name: reach_breakdown reach_breakdown_eu_targeting_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.reach_breakdown
    ADD CONSTRAINT reach_breakdown_eu_targeting_id_fkey FOREIGN KEY (eu_targeting_id) REFERENCES public.eu_targeting(id);


--
-- Name: regional_regulation regional_regulation_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.regional_regulation
    ADD CONSTRAINT regional_regulation_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: targeted_countries targeted_countries_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.targeted_countries
    ADD CONSTRAINT targeted_countries_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: tiktok_ad_details_extra tiktok_ad_details_extra_ad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_details_extra
    ADD CONSTRAINT tiktok_ad_details_extra_ad_id_fkey FOREIGN KEY (ad_id) REFERENCES public.tiktok_ads(ad_id);


--
-- Name: tiktok_ad_media tiktok_ad_media_ad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_media
    ADD CONSTRAINT tiktok_ad_media_ad_id_fkey FOREIGN KEY (ad_id) REFERENCES public.tiktok_ads(ad_id);


--
-- Name: tiktok_ad_targeting_age tiktok_ad_targeting_age_ad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_age
    ADD CONSTRAINT tiktok_ad_targeting_age_ad_id_fkey FOREIGN KEY (ad_id) REFERENCES public.tiktok_ads(ad_id);


--
-- Name: tiktok_ad_targeting_gender tiktok_ad_targeting_gender_ad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_gender
    ADD CONSTRAINT tiktok_ad_targeting_gender_ad_id_fkey FOREIGN KEY (ad_id) REFERENCES public.tiktok_ads(ad_id);


--
-- Name: tiktok_ad_targeting_regions tiktok_ad_targeting_regions_ad_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.tiktok_ad_targeting_regions
    ADD CONSTRAINT tiktok_ad_targeting_regions_ad_id_fkey FOREIGN KEY (ad_id) REFERENCES public.tiktok_ads(ad_id);


--
-- Name: uk_transparency uk_transparency_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.uk_transparency
    ADD CONSTRAINT uk_transparency_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- Name: violation_types violation_types_ad_archive_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: anon-404
--

ALTER TABLE ONLY public.violation_types
    ADD CONSTRAINT violation_types_ad_archive_id_fkey FOREIGN KEY (ad_archive_id) REFERENCES public.ads(ad_archive_id);


--
-- PostgreSQL database dump complete
--

\unrestrict LjHOHtXijc21v81tOEJLhACub6kbOwa51GQeJIRvM2orZiyDjdzKmGzQ2s4kNbF

