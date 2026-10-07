/**
 * Forms to start from: the ones every centre needs (docs/verticali/clinica,
 * requisiti §4). The words are placeholders: the centre's own texts are checked
 * by whoever answers for privacy there before a version is published. ``use`` is
 * the kind of template each one starts: a form of the desk (the default) or one
 * of the website, whose name, email and mobile find the person.
 */

const on = (field, operator, value = '') => [[{ field, operator, value }]]

export const STARTERS = [
  {
    key: 'privacy',
    title: 'Privacy notice and consents',
    description: 'The notice read, marketing yes or no, the signature',
    schema: () => ({
      sections: [
        {
          id: 'privacy',
          title: __('Your data'),
          fields: [
            {
              id: 'notice',
              type: 'paragraph',
              text: __(
                'Write here the privacy notice of the centre: who you are, what you do with the data, for how long, and the rights of the person. Have it checked by whoever answers for privacy.',
              ),
            },
            {
              id: 'notice_read',
              type: 'consent',
              label: __('I have read the privacy notice'),
              consent_type: 'privacy_notice',
              must_accept: true,
            },
            {
              id: 'marketing',
              type: 'consent',
              label: __('News, offers and recalls'),
              consent_type: 'marketing',
              required: true,
            },
            {
              id: 'signature',
              type: 'signature',
              label: __('Signature'),
              signer: 'patient',
              level: 'simple',
              required: true,
            },
          ],
        },
      ],
    }),
  },
  {
    key: 'history',
    title: 'First visit history',
    description: 'Measures, allergies, medications, habits',
    schema: () => ({
      sections: [
        {
          id: 'measures',
          title: __('About you'),
          fields: [
            {
              id: 'weight',
              type: 'number',
              label: __('Weight'),
              unit: 'kg',
              min: 1,
              max: 400,
            },
            {
              id: 'height',
              type: 'number',
              label: __('Height'),
              unit: 'cm',
              min: 30,
              max: 250,
            },
            {
              id: 'bmi',
              type: 'calc',
              label: __('BMI'),
              formula: 'weight / (height / 100) ^ 2',
              decimals: 1,
              unit: 'kg/m²',
            },
          ],
        },
        {
          id: 'health',
          title: __('Your health'),
          fields: [
            {
              id: 'allergies',
              type: 'choice',
              label: __('Allergies'),
              multiple: true,
              options: [
                { label: __('None') },
                { label: __('Medicines') },
                { label: __('Food') },
                { label: __('Latex') },
                { label: __('Other') },
              ],
              required: true,
            },
            {
              id: 'allergies_which',
              type: 'text',
              label: __('Which, and what happens'),
              multiline: true,
              show_if: on('allergies', 'not_equals', __('None')),
            },
            {
              id: 'medications',
              type: 'table',
              label: __('Medications you take'),
              columns: [
                { id: 'name', label: __('Medicine'), type: 'text' },
                { id: 'dose', label: __('How much'), type: 'text' },
                { id: 'since', label: __('Since'), type: 'date' },
              ],
            },
            { id: 'smoker', type: 'yesno', label: __('Do you smoke?') },
            {
              id: 'cigarettes',
              type: 'number',
              label: __('How many a day?'),
              show_if: on('smoker', 'equals', '1'),
            },
          ],
        },
        {
          id: 'signing',
          title: __('Signature'),
          fields: [
            {
              id: 'signature',
              type: 'signature',
              label: __('Signature'),
              signer: 'patient',
              level: 'simple',
              required: true,
            },
          ],
        },
      ],
    }),
  },
  {
    key: 'informed',
    title: 'Informed consent to a treatment',
    description: 'What was explained to this person, their yes, two signatures',
    schema: () => ({
      sections: [
        {
          id: 'treatment',
          title: __('The treatment'),
          fields: [
            {
              id: 'explanation',
              type: 'paragraph',
              text: __(
                'Describe the treatment: what it is, what it is for, the risks and the alternatives, what happens if one does not do it.',
              ),
            },
            {
              // a generic signed form does not prove the person was informed:
              // what was said to this person is written for this person
              id: 'discussed',
              type: 'text',
              label: __('What we discussed with you'),
              multiline: true,
              required: true,
            },
            {
              id: 'pacemaker',
              type: 'yesno',
              label: __('Do you have a pacemaker or another implant?'),
              required: true,
              stop_if: on('pacemaker', 'equals', '1'),
              stop_message: __('Tell the operator before going on'),
            },
            {
              id: 'agree',
              type: 'yesno',
              label: __('I understood and I agree to the treatment'),
              required: true,
              stop_if: on('agree', 'equals', '0'),
              stop_message: __('Without the yes the treatment is not done'),
            },
          ],
        },
        {
          id: 'signing',
          title: __('Signatures'),
          fields: [
            {
              id: 'signature_patient',
              type: 'signature',
              label: __('The patient'),
              signer: 'patient',
              level: 'advanced',
              required: true,
            },
            {
              id: 'signature_operator',
              type: 'signature',
              label: __('The operator'),
              signer: 'operator',
              level: 'simple',
              required: true,
            },
          ],
        },
      ],
    }),
  },
  {
    key: 'questionnaire',
    title: 'Questionnaire before the visit',
    description: 'Pain, and a short scored questionnaire',
    schema: () => {
      const often = [
        { label: __('Never'), score: 0 },
        { label: __('Some days'), score: 1 },
        { label: __('More than half the days'), score: 2 },
        { label: __('Nearly every day'), score: 3 },
      ]
      return {
        sections: [
          {
            id: 'pain',
            title: __('How you are'),
            fields: [
              {
                id: 'pain',
                type: 'scale',
                label: __('Pain today'),
                min: 0,
                max: 10,
                min_label: __('None'),
                max_label: __('The worst'),
              },
              {
                id: 'where',
                type: 'text',
                label: __('Where does it hurt?'),
                show_if: on('pain', 'greater_than', '0'),
              },
            ],
          },
          {
            id: 'weeks',
            title: __('In the last two weeks, how often…'),
            fields: [
              {
                id: 'q1',
                type: 'choice',
                label: __('…did you sleep badly?'),
                options: often,
              },
              {
                id: 'q2',
                type: 'choice',
                label: __('…did you feel tired?'),
                options: often,
              },
              {
                id: 'q3',
                type: 'choice',
                label: __('…was it hard to concentrate?'),
                options: often,
              },
              {
                id: 'total',
                type: 'score',
                label: __('Total'),
                sources: ['q1', 'q2', 'q3'],
                bands: [
                  { from: 0, to: 3, label: __('Low') },
                  { from: 4, to: 6, label: __('Moderate') },
                  { from: 7, to: 9, label: __('High') },
                ],
              },
            ],
          },
        ],
      }
    },
  },
  {
    key: 'contact',
    use: 'Website',
    title: 'Contact request',
    description: 'Name, email, mobile, the request and the news',
    schema: () => ({
      sections: [
        {
          id: 'contact',
          title: '',
          fields: [
            {
              id: 'name',
              type: 'text',
              label: __('Name and surname'),
              person: 'full_name',
              required: true,
            },
            {
              id: 'email',
              type: 'text',
              label: __('Email'),
              person: 'email',
              required: true,
            },
            {
              id: 'mobile',
              type: 'text',
              label: __('Mobile'),
              person: 'mobile_no',
            },
            {
              id: 'request',
              type: 'text',
              label: __('How can we help you?'),
              multiline: true,
              required: true,
            },
            {
              id: 'marketing',
              type: 'consent',
              label: __('News, offers and recalls'),
              consent_type: 'marketing',
            },
          ],
        },
      ],
    }),
  },
  {
    key: 'newsletter',
    use: 'Website',
    title: 'News by email',
    description: 'The name, the email and the consent to news',
    schema: () => ({
      sections: [
        {
          id: 'news',
          title: '',
          fields: [
            {
              id: 'name',
              type: 'text',
              label: __('First name'),
              person: 'first_name',
            },
            {
              id: 'email',
              type: 'text',
              label: __('Email'),
              person: 'email',
              required: true,
            },
            {
              id: 'marketing',
              type: 'consent',
              label: __('News, offers and recalls'),
              consent_type: 'marketing',
              must_accept: true,
            },
          ],
        },
      ],
    }),
  },
]
