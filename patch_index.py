import re

with open('templates/index.html', 'r') as f:
    content = f.read()

start_sig = "function showAdDetail(adId) {"
end_sig = "        // Filter media buttons" # Let's find the end of the function. Wait, let's just find where `function showAdDetail` ends.

# Since `showAdDetail` is quite large, I will use regex or find the matching braces.
# Alternatively, I can just replace everything from `function showAdDetail(adId) {` up to `// Close modal` or whatever the next function is.

def find_closing_brace(s, start_idx):
    count = 0
    for i in range(start_idx, len(s)):
        if s[i] == '{':
            count += 1
        elif s[i] == '}':
            count -= 1
            if count == 0:
                return i
    return -1

start_idx = content.find(start_sig)
brace_idx = content.find('{', start_idx)
end_idx = find_closing_brace(content, brace_idx)

new_function = """function showAdDetail(adId) {
            const entry = allAds.find(a => a.id == adId || a.ad?.id == adId);
            if (!entry) return;

            const ad = entry.ad || entry;
            const raw = ad._raw || {};
            
            const renderVal = (val) => (val !== undefined && val !== null && val !== '') ? val : '–';

            let mainMediaHtml = '';
            let galleryHtml = '';

            if (ad.videos && ad.videos.length > 0) {
                const mainVideo = ad.videos[0].url || ad.videos[0];
                mainMediaHtml = `
                    <div class="modal-media-wrapper">
                        <video src="${mainVideo}" controls autoplay preload="metadata"></video>
                    </div>`;
            } else if (ad.image_urls && ad.image_urls.length > 0) {
                mainMediaHtml = `
                    <div class="modal-media-wrapper">
                        <img src="${ad.image_urls[0]}" alt="Ad Main Image">
                    </div>`;
                if (ad.image_urls.length > 1) {
                    galleryHtml = `<div class="media-gallery">
                        ${ad.image_urls.map((url, i) => `<img src="${url}" onclick="document.querySelector('.modal-media-wrapper img').src='${url}'">`).join('')}
                    </div>`;
                }
            } else {
                mainMediaHtml = `<div class="modal-media-wrapper" style="height:300px; display:flex; align-items:center; justify-content:center; color:#4B5563;">No Media Available</div>`;
            }

            let html = `
                <div class="modal-media-col">
                    <div class="info-title">Creative Assets</div>
                    ${mainMediaHtml}
                    ${galleryHtml}
                    <div style="margin-top:16px;text-align:center;">
                        <img src="${renderVal(ad.advertiser_avatar) !== '–' ? ad.advertiser_avatar : 'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs='}" style="width:60px;height:60px;border-radius:50%;border:2px solid var(--border-color); background: var(--bg-card);">
                        <div style="font-size:0.8em;color:var(--text-secondary);margin-top:4px;">Profile</div>
                    </div>
                </div>
                <div class="modal-info-col">
            `;

            if (ad.platform === 'facebook') {
                const eu = raw.transparency_by_location?.eu_transparency || raw.aaa_info || {};
                const adv = raw.advertiser || {};
                const pageInfo = adv.ad_library_page_info?.page_info || adv.page?.page_info || {};
                const breakdowns = raw.age_country_gender_reach_breakdown || eu.age_country_gender_reach_breakdown || [];
                
                let demoRows = '';
                if (breakdowns.length > 0 && breakdowns[0].age_gender_breakdowns) {
                    breakdowns[0].age_gender_breakdowns.forEach(b => {
                        demoRows += `<tr>
                            <td style="padding:8px;border-bottom:1px solid var(--border-color);">${renderVal(b.age_range)}</td>
                            <td style="padding:8px;border-bottom:1px solid var(--border-color);text-align:center;">${renderVal(b.male)}</td>
                            <td style="padding:8px;border-bottom:1px solid var(--border-color);text-align:center;">${renderVal(b.female)}</td>
                            <td style="padding:8px;border-bottom:1px solid var(--border-color);text-align:center;color:var(--cyan);">${renderVal((b.male || 0) + (b.female || 0))}</td>
                        </tr>`;
                    });
                }

                html += `
                    <div class="info-section">
                        <div class="info-title">Campaign Info</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">Archive ID</div><div class="val">${renderVal(raw.ad_archive_id)}</div></div>
                            <div class="info-item"><div class="lbl">Status</div><div class="val" style="color: ${raw.is_active ? 'var(--success)' : 'inherit'}">${raw.is_active ? '● Active' : '○ Inactive'}</div></div>
                            <div class="info-item"><div class="lbl">Start Date</div><div class="val">${renderVal(raw.start_date_formatted)}</div></div>
                            <div class="info-item"><div class="lbl">End Date</div><div class="val">${renderVal(raw.end_date_formatted)}</div></div>
                            <div class="info-item"><div class="lbl">Total Active Time</div><div class="val">${renderVal(raw.facebook_active_time)}</div></div>
                            <div class="info-item"><div class="lbl">Spend</div><div class="val" style="color:var(--success);">${renderVal(raw.currency)} ${renderVal(raw.spend)}</div></div>
                            <div class="info-item"><div class="lbl">Impressions</div><div class="val">${renderVal(raw.impressions_with_index?.impressions_text || raw.impressions)}</div></div>
                            <div class="info-item"><div class="lbl">Gated Type</div><div class="val">${renderVal(raw.gated_type)}</div></div>
                            <div class="info-item"><div class="lbl">Eligible AAA</div><div class="val">${renderVal(raw.is_aaa_eligible)}</div></div>
                            <div class="info-item"><div class="lbl">Digital Media</div><div class="val">${renderVal(raw.contains_digital_created_media)}</div></div>
                            <div class="info-item"><div class="lbl">Sensitive Content</div><div class="val">${renderVal(raw.contains_sensitive_content)}</div></div>
                            <div class="info-item"><div class="lbl">Hide Data Status</div><div class="val">${renderVal(raw.hide_data_status)}</div></div>
                            <div class="info-item"><div class="lbl">State Media Run</div><div class="val">${renderVal(raw.state_media_run_label)}</div></div>
                            <div class="info-item"><div class="lbl">Collation Count</div><div class="val">${renderVal(raw.collation_count)}</div></div>
                            <div class="info-item"><div class="lbl">Ads Count</div><div class="val">${renderVal(raw.ads_count)}</div></div>
                        </div>
                    </div>

                    <div class="info-section">
                        <div class="info-title">Advertiser</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">Page ID</div><div class="val">${renderVal(pageInfo.page_id)}</div></div>
                            <div class="info-item"><div class="lbl">Page Name</div><div class="val">${renderVal(pageInfo.page_name)}</div></div>
                            <div class="info-item"><div class="lbl">Category</div><div class="val">${renderVal(pageInfo.page_category)}</div></div>
                            <div class="info-item"><div class="lbl">Alias</div><div class="val">${renderVal(pageInfo.page_alias)}</div></div>
                            <div class="info-item"><div class="lbl">Likes</div><div class="val">${renderVal(pageInfo.likes)}</div></div>
                            <div class="info-item"><div class="lbl">IG Followers</div><div class="val">${renderVal(pageInfo.ig_followers)}</div></div>
                            <div class="info-item"><div class="lbl">IG Username</div><div class="val">${renderVal(pageInfo.ig_username)}</div></div>
                            <div class="info-item"><div class="lbl">Verification</div><div class="val">${renderVal(pageInfo.page_verification)}</div></div>
                            <div class="info-item"><div class="lbl">Profile URI</div><div class="val"><a href="${renderVal(pageInfo.page_profile_uri)}" target="_blank">${renderVal(pageInfo.page_profile_uri)}</a></div></div>
                            <div class="info-item"><div class="lbl">Political Page</div><div class="val">${renderVal(pageInfo.page_spend?.is_political_page)}</div></div>
                        </div>
                    </div>
                `;

                const creativeCards = raw.snapshot?.cards || raw.cards || [];
                if (creativeCards.length > 0) {
                    html += `<div class="info-section"><div class="info-title">Ad Creative Cards</div>`;
                    creativeCards.forEach((card, idx) => {
                        html += `
                        <div style="background:var(--bg-input);border:1px solid var(--border-color);border-radius:12px;padding:16px;margin-bottom:12px;">
                            <div style="font-weight:600;margin-bottom:8px;color:var(--text-primary);">Card ${idx + 1}</div>
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>Title:</strong> ${renderVal(card.title)}</div>
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>Body:</strong> ${renderVal(card.body)}</div>
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>CTA:</strong> ${renderVal(card.ctaText || card.cta_text)}</div>
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>Link:</strong> <a href="${renderVal(card.linkUrl || card.link_url)}" target="_blank">${renderVal(card.linkUrl || card.link_url)}</a></div>
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>Caption:</strong> ${renderVal(card.caption)}</div>
                            <div style="font-size:0.85em;color:var(--cyan);margin-bottom:4px;"><strong>Link Desc:</strong> ${renderVal(card.link_description)}</div>
                        </div>`;
                    });
                    html += `</div>`;
                } else {
                     html += `<div class="info-section"><div class="info-title">Ad Creative Snapshot</div>
                     <div style="background:var(--bg-input);border:1px solid var(--border-color);border-radius:12px;padding:16px;margin-bottom:12px;">
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>Title:</strong> ${renderVal(raw.snapshot?.title)}</div>
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>Body:</strong> ${renderVal(raw.snapshot?.body)}</div>
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>Caption:</strong> ${renderVal(raw.snapshot?.caption)}</div>
                            <div style="font-size:0.85em;color:var(--text-secondary);margin-bottom:4px;"><strong>Link URL:</strong> ${renderVal(raw.snapshot?.link_url)}</div>
                        </div></div>`;
                }

                html += `
                    <div class="info-section">
                        <div class="info-title">Platforms</div>
                        <div>
                            ${(raw.publisher_platform || []).map(p => `<span class="badge facebook" style="margin-right:4px;">${p}</span>`).join('') || '–'}
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <div class="info-title">EU Targeting & Transparency</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">EU Total Reach</div><div class="val" style="color:var(--cyan);">${renderVal(raw.eu_total_reach || eu.eu_total_reach)}</div></div>
                            <div class="info-item"><div class="lbl">Gender</div><div class="val">${renderVal(eu.gender_audience || raw.gender_audience)}</div></div>
                            <div class="info-item"><div class="lbl">Age Min</div><div class="val">${renderVal(eu.age_audience?.min || raw.age_audience?.min)}</div></div>
                            <div class="info-item"><div class="lbl">Age Max</div><div class="val">${renderVal(eu.age_audience?.max || raw.age_audience?.max)}</div></div>
                            <div class="info-item"><div class="lbl">Targets EU</div><div class="val">${renderVal(eu.targets_eu)}</div></div>
                            <div class="info-item"><div class="lbl">Payer</div><div class="val">${renderVal(eu.payer_beneficiary_data?.[0]?.payer)}</div></div>
                            <div class="info-item"><div class="lbl">Beneficiary</div><div class="val">${renderVal(eu.payer_beneficiary_data?.[0]?.beneficiary)}</div></div>
                        </div>
                        ${demoRows ? `<table style="width:100%;margin-top:16px;border-collapse:collapse;background:var(--bg-input);border-radius:12px;overflow:hidden;">
                                <thead>
                                    <tr style="background:var(--border-color);">
                                        <th style="padding:12px;text-align:left;font-size:0.85em;color:var(--text-secondary);">Age</th>
                                        <th style="padding:12px;text-align:center;font-size:0.85em;color:var(--text-secondary);">Male</th>
                                        <th style="padding:12px;text-align:center;font-size:0.85em;color:var(--text-secondary);">Female</th>
                                        <th style="padding:12px;text-align:center;font-size:0.85em;color:var(--cyan);">Total</th>
                                    </tr>
                                </thead>
                                <tbody style="color:var(--text-primary);">${demoRows}</tbody>
                            </table>` : '<div style="margin-top:16px;color:var(--text-secondary);">No demographic breakdown available.</div>'}
                    </div>

                    <div class="info-section">
                        <div class="info-title">Regulation & Flags</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">FinServ Deemed</div><div class="val">${renderVal(raw.regional_regulation_data?.finserv_is_deemed_finserv)}</div></div>
                            <div class="info-item"><div class="lbl">FinServ Limited</div><div class="val">${renderVal(raw.regional_regulation_data?.finserv_is_limited_delivery)}</div></div>
                            <div class="info-item"><div class="lbl">TW Anti Scam</div><div class="val">${renderVal(raw.regional_regulation_data?.tw_anti_scam_is_limited_delivery)}</div></div>
                            <div class="info-item"><div class="lbl">Violating EU SIEP</div><div class="val">${renderVal(raw.is_violating_eu_siep)}</div></div>
                            <div class="info-item"><div class="lbl">Violating Payer/Beneficiary</div><div class="val">${renderVal(eu.has_violating_payer_beneficiary)}</div></div>
                            <div class="info-item"><div class="lbl">Taken Down</div><div class="val">${renderVal(eu.is_ad_taken_down)}</div></div>
                            <div class="info-item" style="grid-column: 1/-1;"><div class="lbl">Violation Types</div><div class="val">${(raw.violation_types || []).join(', ') || '–'}</div></div>
                        </div>
                    </div>

                    <div class="info-section">
                        <div class="info-title">Raw Extra Content</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">Extra Links</div><div class="val">${renderVal(raw.extra_links)}</div></div>
                            <div class="info-item"><div class="lbl">Extra Texts</div><div class="val">${renderVal(raw.extra_texts)}</div></div>
                            <div class="info-item"><div class="lbl">Extra Images</div><div class="val">${renderVal(raw.extra_images)}</div></div>
                            <div class="info-item"><div class="lbl">Extra Videos</div><div class="val">${renderVal(raw.extra_videos)}</div></div>
                        </div>
                    </div>

                    <div class="info-section">
                        <div class="info-title">Metadata & Archive</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">Ad ID</div><div class="val">${renderVal(raw.ad_id)}</div></div>
                            <div class="info-item"><div class="lbl">Fev Info</div><div class="val">${renderVal(raw.fev_info)}</div></div>
                            <div class="info-item"><div class="lbl">Verified Voice</div><div class="val">${renderVal(raw.verified_voice_context)}</div></div>
                            <div class="info-item"><div class="lbl">Branded Content</div><div class="val">${renderVal(raw.snapshot?.branded_content)}</div></div>
                            <div class="info-item"><div class="lbl">Byline</div><div class="val">${renderVal(raw.snapshot?.byline)}</div></div>
                            <div class="info-item"><div class="lbl">Disclaimer</div><div class="val">${renderVal(raw.snapshot?.disclaimer_label)}</div></div>
                            <div class="info-item"><div class="lbl">Root Reshared Post</div><div class="val">${renderVal(raw.snapshot?.root_reshared_post)}</div></div>
                            <div class="info-item"><div class="lbl">Event</div><div class="val">${renderVal(raw.snapshot?.event)}</div></div>
                            <div class="info-item"><div class="lbl">Brazil Tax ID</div><div class="val">${renderVal(raw.snapshot?.brazil_tax_id)}</div></div>
                            <div class="info-item"><div class="lbl">Additional Info</div><div class="val">${renderVal(raw.snapshot?.additional_info)}</div></div>
                            <div class="info-item"><div class="lbl">EC Certificates</div><div class="val">${renderVal(raw.snapshot?.ec_certificates)}</div></div>
                            <div class="info-item"><div class="lbl">Categories</div><div class="val">${(raw.categories || []).join(', ') || '–'}</div></div>
                            <div class="info-item"><div class="lbl">Targeted Countries</div><div class="val">${(raw.targeted_or_reached_countries || []).join(', ') || '–'}</div></div>
                        </div>
                        <div style="background:var(--bg-input);padding:16px;border-radius:12px;border:1px solid var(--border-color); margin-top: 16px;">
                            <a href="${renderVal(raw.ad_library_url)}" target="_blank" style="color:var(--accent-primary);word-break:break-all;">${renderVal(raw.ad_library_url)}</a>
                        </div>
                    </div>
                `;
            } else if (ad.platform === 'tiktok') {
                const targetRegions = raw['Ad Targeting']?.regions || [];
                const targetAge = raw['Ad Targeting']?.age || [];
                const targetGender = raw['Ad Targeting']?.gender || [];
                const detailsMap = (raw['Ad Details'] || []).reduce((acc, curr) => ({...acc, ...curr}), {});

                // Combine targeting into rows
                let targetingRows = '';
                if (targetRegions.length > 0) {
                    targetRegions.forEach(tr => {
                        const ageObj = targetAge.find(a => a.region === tr.region) || {};
                        const genObj = targetGender.find(g => g.region === tr.region) || {};
                        
                        let ages = [];
                        if (ageObj['13-17']) ages.push('13-17');
                        if (ageObj['18-24']) ages.push('18-24');
                        if (ageObj['25-34']) ages.push('25-34');
                        if (ageObj['35-44']) ages.push('35-44');
                        if (ageObj['45-54']) ages.push('45-54');
                        if (ageObj['55+']) ages.push('55+');
                        
                        let genders = [];
                        if (genObj.male) genders.push('Male');
                        if (genObj.female) genders.push('Female');
                        if (genObj.unknown) genders.push('Unknown');
                        
                        targetingRows += `<tr>
                            <td style="padding:8px;border-bottom:1px solid var(--border-color);">${renderVal(tr.region)}</td>
                            <td style="padding:8px;border-bottom:1px solid var(--border-color);">${renderVal(tr.impressions)}</td>
                            <td style="padding:8px;border-bottom:1px solid var(--border-color);">${ages.map(a => `<span class="badge">${a}</span>`).join('') || '–'}</td>
                            <td style="padding:8px;border-bottom:1px solid var(--border-color);">${genders.join(', ') || '–'}</td>
                        </tr>`;
                    });
                }

                html += `
                    <div class="info-section">
                        <div class="info-title">Campaign Info</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">Ad ID</div><div class="val">${renderVal(raw['AD ID'])}</div></div>
                            <div class="info-item"><div class="lbl">Status</div><div class="val" style="color:var(--success);">● Active</div></div>
                            <div class="info-item"><div class="lbl">First Shown Date</div><div class="val">${renderVal(raw['Ad Dates']?.[0]?.FirstShown)}</div></div>
                            <div class="info-item"><div class="lbl">Last Shown Date</div><div class="val">${renderVal(raw['Ad Dates']?.[0]?.LastShown)}</div></div>
                            <div class="info-item"><div class="lbl">Ad Type</div><div class="val">${renderVal(detailsMap['Type'])}</div></div>
                            <div class="info-item"><div class="lbl">Audit Status</div><div class="val">${renderVal(detailsMap['Audit Status'])}</div></div>
                        </div>
                    </div>

                    <div class="info-section">
                        <div class="info-title">Advertiser</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">Advertiser Name</div><div class="val">${renderVal(raw['Advertiser Name'])}</div></div>
                            <div class="info-item"><div class="lbl">Sponsor</div><div class="val">${renderVal(raw['Ad Sponsor'])}</div></div>
                            <div class="info-item"><div class="lbl">Target Audience Size</div><div class="val">${renderVal(raw['Ad Target Audience Size'])}</div></div>
                        </div>
                    </div>
                    
                    <div class="info-section">
                        <div class="info-title">Creative Details</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">Videos count</div><div class="val">${ad.videos ? ad.videos.length : 0} videos</div></div>
                            <div class="info-item"><div class="lbl">Images count</div><div class="val">${ad.image_urls ? ad.image_urls.length : 0} images</div></div>
                        </div>
                    </div>

                    <div class="info-section">
                        <div class="info-title">Audience & Reach</div>
                        <div class="info-grid">
                            <div class="info-item"><div class="lbl">Ad Audience (Reach Estimate)</div><div class="val" style="color:var(--cyan);">${renderVal(raw['Ad Audience'])}</div></div>
                            <div class="info-item"><div class="lbl">Impression</div><div class="val">${renderVal(detailsMap['Impression'])}</div></div>
                            <div class="info-item"><div class="lbl">Spent</div><div class="val" style="color:var(--success);">${renderVal(detailsMap['Spent'])}</div></div>
                        </div>
                    </div>

                    <div class="info-section">
                        <div class="info-title">Targeting by Region</div>
                        ${targetingRows ? `<table style="width:100%;border-collapse:collapse;background:var(--bg-input);border-radius:12px;overflow:hidden;">
                                <thead>
                                    <tr style="background:var(--border-color);">
                                        <th style="padding:12px;text-align:left;font-size:0.85em;color:var(--text-secondary);">Region</th>
                                        <th style="padding:12px;text-align:left;font-size:0.85em;color:var(--text-secondary);">Impressions</th>
                                        <th style="padding:12px;text-align:left;font-size:0.85em;color:var(--text-secondary);">Active Age Ranges</th>
                                        <th style="padding:12px;text-align:left;font-size:0.85em;color:var(--text-secondary);">Genders Targeted</th>
                                    </tr>
                                </thead>
                                <tbody style="color:var(--text-primary);">${targetingRows}</tbody>
                            </table>` : '<div style="color:var(--text-secondary);">No targeting data available.</div>'}
                    </div>

                    <div class="info-section">
                        <div class="info-title">Library Link</div>
                        <div style="background:var(--bg-input);padding:16px;border-radius:12px;border:1px solid var(--border-color);">
                            <a href="${renderVal(raw['Ad Detail URL'])}" target="_blank" style="color:var(--accent-primary);word-break:break-all;">${renderVal(raw['Ad Detail URL'])}</a>
                        </div>
                    </div>
                `;
            }

            html += `</div>`; // Close modal-info-col
            document.getElementById('modal_body').innerHTML = html;
            document.getElementById('modal').classList.add('show');
        }"""

new_content = content[:start_idx] + new_function + content[end_idx+1:]

with open('templates/index.html', 'w') as f:
    f.write(new_content)
