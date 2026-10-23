---
title: "{{ replace .Name "-" " " | title }}"
date: {{ .Date | time.AsTime | time.In "Asia/Tokyo" | time.Format "2006-01-02T15:04:05Z07:00" }}
draft: true
description: ""
categories: []
tags: []
audiences: ["technical"]
companion: ""
---
