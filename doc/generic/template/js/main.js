// globals

// to be compliant with python types (from JSON log)
const False = false
const True = true
const nan = NaN
const None = "None"

function plotBinaryConfusionMatrix(cm) {

    let z = [
        [cm['c01'], cm['c00']],
        [cm['c11'], cm['c10']],
    ]
    let annotations = []

    for (let i = 0; i < 2; i++) {
        for (let j = 0; j < 2; j++) {
            annotations.push({ x: j, y: i, text: z[i][j], showarrow: false, font: { color: 'white' } })
            z[i][j] = 1 // correct label
        }
        z[i][i] = 0 // wrong label
    }

    let data = [{
        z: z,
        x: ['c1', 'c0'],
        y: ['c0', 'c1'],
        type: 'heatmap',
        colorscale: [[0, '#900'], [1, '#009']],
        hoverongaps: false,
        zmin: 0,
        zmax: 1,
        showscale: false
    }];
    var layout = {
        annotations: annotations,
        autosize: false,
        margin: { l: 400 },
        width: 750,
        height: 350,
        xaxis: { title: { text: 'Predito' } },
        yaxis: { title: { text: 'Real' } },
    };
    var config = {
        staticPlot: true,
    }
    Plotly.newPlot(`chart-confusion-matrix`, data, layout, config);
}

function buildKeyValueTableBody(dict, tbodyId) {
    const tbody = document.getElementById(tbodyId)
    Object.keys(dict).forEach((key) => {
        let row = document.createElement('tr')
        let tdkey = document.createElement('td')
        tdkey.innerHTML = `<samp>${key}</samp>`
        row.appendChild(tdkey)
        let tdvalue = document.createElement('td')
        tdvalue.innerHTML = `<code>${dict[key]}</code>`
        row.appendChild(tdvalue)
        tbody.appendChild(row)
    })
}

function buildTableOfModels(ranking) {
    
    const models = Object.keys(ranking)
    document.getElementById('models-qtd').innerText = models.length
    
    const tbody = document.getElementById('table-models-body')
    
    models.forEach((key) => {
        let row = document.createElement('tr')
        let tdmodel = document.createElement('td')
        tdmodel.innerText = key
        row.appendChild(tdmodel)
        
        let tdmetric = document.createElement('td')
        tdmetric.innerText = ranking[key]
        row.appendChild(tdmetric)
        
        tbody.appendChild(row)
    })
}

function plotCorrelation(obj, name, colorscale = "RdBu", zmin = 0, zmax = 1) {

    const labels = []
    const correlations = []
    const annotations = []

    Object.keys(obj).forEach(row => {
        let values = []
        labels.push(row)
        correlations.push(values)
        Object.keys(obj[row]).forEach(col => {
            values.push(obj[row][col])
            annotations.push({ x: row, y: col, text: obj[row][col].toFixed(2), showarrow: false, font: { color: 'white' } })
        })
    })

    let data = [{
        z: correlations,
        x: labels,
        y: labels,
        type: 'heatmap',
        colorscale: colorscale,
        hoverongaps: false,
        zmin: zmin,
        zmax: zmax
    }];
    var layout = {
        annotations: annotations,
        autosize: false,
        margin: { l: 200 },
        width: 700,
        height: 450
    };
    var config = {
        staticPlot: true
    }
    Plotly.newPlot(`variable-correlations-${name}`, data, layout, config);

}

function getMessageText(message) {
    switch (message.type) {
        case "HIGH_CARDINALITY":
            return "Alta cardinalidade"
        case "MISSING":
            return "Valores ausentes"
        case "UNIFORM":
            return "Uniformemente distribuída"
        case "UNIQUE":
            return "Valores únicos"
        case "ZEROS":
            return "Possui zeros"
    }
}

function appendMessages(messages) {

    messages.forEach(message => {
        let messageBox = document.getElementById(`var-${message.column}-messages`)
        let badge = `<span class="badge badge-warning">${getMessageText(message)}</span>`
        messageBox.innerHTML += badge
    })
}

function numericSummary(varDiv, variable) {
    varDiv.innerHTML += `
        <table class="table table-borderless table-sm">
            <tr><th>Máximo: </th><td>${(variable.max).toFixed(2)}</td></tr>
            <tr><th>Mínimo: </th><td>${(variable.min).toFixed(2)}</td></tr>
            <tr><th>Média: </th><td>${(variable.mean).toFixed(2)}</td></tr>
            <tr><th>Desvio padrão: </th><td>${(variable.std).toFixed(2)}</td></tr>
        </table>
    `
}

function distinctAndMissingSummary(variable, key) {
    return `
        <table class="table table-borderless table-sm">
            <tr>
                <th>Distintos: </th> 
                <td> 
                    ${variable.distinct_count_with_nan} 
                    <span class="text-muted">(${((variable.distinct_count_with_nan / variable.n) * 100).toFixed(2)}%) </span>
                </td>
            </tr>
            <tr>
                <th>Ausentes: </th> 
                <td> 
                    ${variable.n_missing} 
                    <span class="text-muted">(${((variable.n_missing / variable.n) * 100).toFixed(2)}%) </span>
                </td>
            </tr>
            <tr>
                <td colspan="2" id="var-${key}-messages"></td>
            </tr>
        </table>
    `

}

function plotHistogram(div, variable, key) {
    const plotDiv = document.createElement('div')
    const divId = `div-var-${key}`
    plotDiv.id = divId
    div.appendChild(plotDiv)

    const trace = {
        x: variable.histogram_data,
        type: 'histogram',
    }
    const data = [trace]
    var layout = {
        title: {
            text: 'Histograma',
            size: 12,
        },
        autosize: true,
        margin: { l: 30, r: 10, t: 25, b: 20 },
        width: 300,
        height: 125,
    };
    var config = {
        staticPlot: true
    }
    Plotly.newPlot(divId, data, layout, config)
}

function plotValueCounts(div, variable, key) {
    const plotDiv = document.createElement('div')
    const divId = `div-var-${key}`
    plotDiv.id = divId
    div.appendChild(plotDiv)

    let items = Object.keys(variable.value_counts).map(k => {
        return { 'key': k + " -", 'value': variable.value_counts[k] }
    })
    items = items.sort((a, b) => a.value - b.value)

    let maxItems = 5
    if (variable.n_missing > 0) {
        maxItems = 4
    }

    if (items.length > maxItems) {
        const others = items.slice(0, items.length - maxItems + 1)
        othersValue = others.reduce((acc, item) => acc + item.value, 0)
        items = items.slice(items.length - maxItems + 1, items.length)
        items.push({ 'key': 'Outros valores' + " -", 'value': othersValue })
    }

    if (variable.n_missing > 0) {
        items.push({ 'key': 'Valores ausentes' + " -", 'value': variable.n_missing })
    }

    let keys = [],
        values = []

    items.forEach(i => {
        keys.push(i.key)
        values.push(i.value)
    })

    let data = [{
        x: values,
        y: keys,
        type: 'bar',
        orientation: 'h'
    }];
    var layout = {
        title: {
            text: 'Contagem',
            size: 12,
        },
        autosize: true,
        margin: { l: 230, r: 10, t: 25, b: 20 },
        width: 500,
        height: 125,
    };
    var config = {
        staticPlot: true
    }
    Plotly.newPlot(divId, data, layout, config);
}

function buildVariableProfiling(profiling) {

    const div = document.getElementById('varialbe-profiling-div')

    Object.keys(profiling).forEach(key => {
        const variable = profiling[key]

        const box = document.createElement('tr')
        box.classList.add('unbreakable-on-print')
        box.classList.add('border-light-gray')
        div.appendChild(box)

        box.innerHTML = `<p><span class="h4">${key}</span><span class="text-muted"> (${variable.type})</span></p>`

        const row = document.createElement('td')
        row.classList.add('row')
        box.appendChild(row)

        const summary = document.createElement('div')
        summary.classList.add('col')
        row.appendChild(summary)

        summary.innerHTML += distinctAndMissingSummary(variable, key)

        if (variable.type === 'NUM') {
            const details = document.createElement('div')
            details.classList.add('col')
            row.appendChild(details)
            numericSummary(details, variable, key)

            const plot = document.createElement('div')
            plot.classList.add('col')
            row.appendChild(plot)
            plotHistogram(plot, variable, key)
        } else {
            const plot = document.createElement('div')
            plot.classList.add('col')
            row.appendChild(plot)
            plotValueCounts(plot, variable, key)
        }
    })

}

function appendTableData(text, clazz, row) {
    let td = document.createElement('td')
    td.innerText = text
    td.classList.add(clazz)
    row.appendChild(td)
}

function buildTargetTreatmentsTable(labels, counts, total) {
    let tbody = document.getElementById('target-treatments-tbody')

    for (let key in labels) {
        let tr = document.createElement('tr')

        appendTableData(labels[key], 'td-categ', tr)
        appendTableData(key, 'td-categ', tr)
        appendTableData(counts[key], 'td-number', tr)
        appendTableData(`${(counts[key] / total * 100).toFixed(2)}%`, 'td-number', tr)

        tbody.appendChild(tr)
    }
}

function filterToRecommendedSummary(variableTreatments, filterToRecommened) {

    let values = variableTreatments.recommended
    let nvariables = Object.keys(values).length
    let countRecommended = Object.keys(values).reduce((acc, key) => acc + values[key], 0)
    let countNotRecommened = nvariables - countRecommended

    let message = `Das ${nvariables} variáveis, ${countRecommended} foram recomendadas, por terem variabilidade e significância. Enquanto ${countNotRecommened} não foram recomendadas.`
    if (filterToRecommened.toLowerCase() === "true") {
        message += ` Apenas as ${countRecommended} variáveis recomendadas foram mantidas no modelo.`
    } else {
        message += ` Apesar da recomendação, as ${countNotRecommened} variáveis não recomendadas foram mantidas no modelo.`
    }
    document.getElementById('filter-to-recommended').innerText = message
}

function fillMinMaxSummary(variables, values, messageTemplate, decimalPlaces = 2) {

    let keyValuePairs = Object.keys(values).map(k => { return { 'key': k, 'value': values[k] } })
    let max = keyValuePairs.reduce((acc, cur) => (cur.value !== null && Math.abs(cur.value) >= Math.abs(acc.value)) ? cur : acc)
    let min = keyValuePairs.reduce((acc, cur) => (cur.value !== null && Math.abs(cur.value) <= Math.abs(acc.value)) ? cur : acc)

    return messageTemplate.replace('$max-key$', variables[max.key])
        .replace('$max-signal$', max.value > 0 ? 'positiva' : 'negativa')
        .replace('$max-value$', max.value.toFixed(decimalPlaces))
        .replace('$min-key$', variables[min.key])
        .replace('$min-value$', min.value.toFixed(decimalPlaces))
}

function writePearsonSummary(variableTreatments) {
    document.getElementById('pearson-summary').innerHTML = fillMinMaxSummary(
        variableTreatments.variable,
        variableTreatments.PearsonR,
        `A variável com maior correlação de Pearson foi <samp>$max-key$</samp>, com correlação $max-signal$ de $max-value$. 
        Enquanto a variável com menor correlação foi <samp>$min-key$</samp>, com $min-value$.`)
}

function writeRSquaredSummary(variableTreatments) {
    document.getElementById('r-squared-summary').innerHTML = fillMinMaxSummary(
        variableTreatments.variable,
        variableTreatments.R2,
        `Para o R-quadrado, a variável com maior valor foi <samp>$max-key$</samp>, com $max-value$. 
        Enquanto a variável com menor valor foi <samp>$min-key$</samp>, com $min-value$.`)
}

function buildTableFromVariableTreatmentData(variableTreatments, tbodyId, ...columns) {

    let tbody = document.getElementById(tbodyId)
    let nvariables = Object.keys(variableTreatments.variable).length

    for (let i = 0; i < nvariables; i++) {
        let tr = document.createElement('tr')
        let th = document.createElement('td')
        th.scope = 'row'
        th.innerText = variableTreatments.variable[i]
        tr.appendChild(th)

        for (let col of columns) {
            let td = document.createElement('td')
            if (variableTreatments[col][i] === true) {
                td.classList.add('td-bool')
                td.classList.add('td-true')
            } else if (variableTreatments[col][i] === false) {
                td.classList.add('td-bool')
                td.classList.add('td-false')
            } else if (typeof variableTreatments[col][i] === 'number') {
                if (isNaN(variableTreatments[col][i])) {
                    td.classList.add('td-null')
                } else {
                    td.innerText = variableTreatments[col][i].toFixed(4)
                    td.classList.add('td-number')
                }
            } else {
                td.innerText = variableTreatments[col][i]
            }
            tr.appendChild(td)
        }

        tbody.appendChild(tr)
    }
}


function plotFeatureImportances(featureImportances, maxNumberOfVariablesToPlot = 10) {

    let message = `Neste gráfico são apresentadas as ${maxNumberOfVariablesToPlot} variáveis mais importantes.`

    let items = Object.keys(featureImportances).map(k => {
        return { 'key': k, 'value': featureImportances[k] }
    })
    items = items.sort((a, b) => a.value - b.value)

    if (items.length > maxNumberOfVariablesToPlot) {
        items = items.slice(items.length - maxNumberOfVariablesToPlot, items.length)
        let obs = document.getElementById('obs-number-of-variables')
        obs.innerText = message
    }

    let keys = [],
        values = []

    items.forEach(i => {
        keys.push(i.key)
        values.push(i.value)
    })

    let data = [{
        x: values,
        y: keys,
        type: 'bar',
        orientation: 'h'
    }];
    var layout = {
        autosize: false,
        margin: { l: 200 },
        width: 700,
        height: 450
    };
    var config = {
        staticPlot: true
    }
    Plotly.newPlot('chart-feature-importances', data, layout, config);
}